from datetime import timedelta

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class TestWooeyJobSubmissionFieldsMigration(TransactionTestCase):
    migrate_from = (("wooey", "0055_add_wooeyjob_retry_fields"),)
    migrate_to = (("wooey", "0058_finalize_wooeyjob_submitted_date"),)

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        ScriptGroup = old_apps.get_model("wooey", "ScriptGroup")
        Script = old_apps.get_model("wooey", "Script")
        ScriptVersion = old_apps.get_model("wooey", "ScriptVersion")
        WooeyJob = old_apps.get_model("wooey", "WooeyJob")

        group = ScriptGroup.objects.create(group_name="migration", slug="migration")
        script = Script.objects.create(
            script_name="migration",
            slug="migration",
            script_group=group,
        )
        script_version = ScriptVersion.objects.create(
            script=script,
            script_path="migration.py",
            checksum="migration",
        )
        job = WooeyJob.objects.create(
            script_version=script_version,
            job_name="migration",
            command="",
        )
        self.created_date = timezone.now() - timedelta(days=2)
        WooeyJob.objects.filter(pk=job.pk).update(created_date=self.created_date)
        self.job_pk = job.pk

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_backfills_submitted_date_from_created_date(self):
        WooeyJob = self.apps.get_model("wooey", "WooeyJob")

        job = WooeyJob.objects.get(pk=self.job_pk)

        self.assertEqual(job.submitted_date, self.created_date)
        self.assertIsNone(job.submission_id)
