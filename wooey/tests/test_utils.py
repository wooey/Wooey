import os
import six
import zipfile

from django.test import TestCase

from ..backend import utils

from . import factories
from . import config
from . import mixins


class TestUtils(mixins.ScriptFactoryMixin, mixins.FileMixin, TestCase):
    def test_sanitize_name(self):
        assert(utils.sanitize_name('abc')) == 'abc'
        assert(utils.sanitize_name('ab c')) == 'ab_c'
        assert(utils.sanitize_name('ab-c')) == 'ab_c'

    def test_sanitize_string(self):
        assert(utils.sanitize_string('ab"c')) == 'ab\\"c'

    def test_anonymous_users(self):
        from .. import settings as wooey_settings
        from django.contrib.auth.models import AnonymousUser
        user = AnonymousUser()
        script_version = self.translate_script
        script = script_version.script
        d = utils.valid_user(script, user)
        self.assertTrue(d['valid'])
        wooey_settings.WOOEY_ALLOW_ANONYMOUS = False
        d = utils.valid_user(script, user)
        self.assertFalse(d['valid'])

    def test_valid_user(self):
        user = factories.UserFactory()
        script_version = self.translate_script
        script = script_version.script
        d = utils.valid_user(script, user)
        self.assertTrue(d['valid'])
        from .. import settings as wooey_settings
        self.assertEqual('disabled', d['display'])
        wooey_settings.WOOEY_SHOW_LOCKED_SCRIPTS = False
        d = utils.valid_user(script, user)
        self.assertEqual('hide', d['display'])
        from django.contrib.auth.models import Group
        test_group = Group(name='test')
        test_group.save()
        script.user_groups.add(test_group)
        d = utils.valid_user(script, user)
        self.assertFalse(d['valid'])
        user.groups.add(test_group)
        d = utils.valid_user(script, user)
        self.assertTrue(d['valid'])

    def test_job_file_outputs(self):
        # Run a script that creates a file
        from wooey.models import WooeyJob, UserFile
        script = os.path.join(config.WOOEY_TEST_SCRIPTS, 'file_maker.py')
        with open(script) as o:
            new_file = self.storage.save(self.filename_func('file_maker.py'), o)
        res = utils.add_wooey_script(script_path=new_file, group=None)
        self.assertEqual(res['valid'], True, res['errors'])
        job = utils.create_wooey_job(
            script_version_pk=res['script'].pk,
            data={'job_name': 'abc'}
        )
        # Get the new job
        job.submit_to_celery()
        job = WooeyJob.objects.get(pk=job.pk)
        utils.create_job_fileinfo(job)

        # Make sure the file info is correct
        self.assertEqual(UserFile.objects.filter(job=job).count(), 4)
        for job_file in UserFile.objects.filter(job=job):
            wooey_file = job_file.system_file
            self.assertEqual(
                os.path.getsize(self.storage.path(wooey_file.filepath.name)),
                wooey_file.size_bytes,
            )

        # Check for the zip file overwrite in for https://github.com/wooey/Wooey/issues/202
        zip_file = UserFile.objects.get(job=job, filename__endswith='zip')
        _zip = zipfile.ZipFile(zip_file.system_file.filepath)
        files = [filename.filename for filename in _zip.filelist]
        six.assertCountEqual(self, files, ['abc/', 'abc/test_file', 'abc/test_dir/test_file'])

    def test_duplicate_scriptversion_checksums(self):
        # Tests that script versions with duplicate checksums are correctly returned
        script = os.path.join(config.WOOEY_TEST_SCRIPTS, 'versioned_script', 'v1.py')
        with open(script) as o:
            v1 = self.storage.save(self.filename_func('v1.py'), o)
        res = utils.add_wooey_script(script_path=v1, script_name='test_versions')
        first_version = res['script']
        first_version_pk = first_version.pk
        self.assertEqual(res['valid'], True, res['errors'])

        # Force a duplication of the Script Version, this mimics legacy code that may
        # have several script versions that were uploaded.

        first_version.pk = None
        first_version.script_iteration = first_version.script_iteration + 1
        first_version.save()
        second_version_pk = first_version.pk

        # Add the script again, which should not fail on MultipleObjectsReturned
        res = utils.add_wooey_script(script_path=v1, script_name='test_versions')
        self.assertEqual(res['script'].pk, second_version_pk)

    def test_add_wooey_script(self):
        from wooey.models import ScriptParser, ScriptVersion
        script = os.path.join(config.WOOEY_TEST_SCRIPTS, 'versioned_script', 'v1.py')
        with open(script) as o:
            v1 = self.storage.save(self.filename_func('v1.py'), o)
        res = utils.add_wooey_script(script_path=v1, script_name='test_versions')
        first_version = res['script']
        self.assertEqual(res['valid'], True, res['errors'])
        parser = ScriptParser.objects.get(script_version=res['script'])
        self.assertEqual(parser.name, u'')

        # Test that adding the script again doesn't update anything
        res = utils.add_wooey_script(script_path=v1, script_name='test_versions')
        self.assertEqual(res['valid'], False)
        self.assertEqual(str(res['errors']), ScriptVersion.error_messages['duplicate_script'])
        dup_first_version = res['script']
        self.assertEqual(
            first_version.script_version,
            dup_first_version.script_version
        )
        self.assertEqual(first_version.script_iteration, 1)
        self.assertEqual(dup_first_version.script_iteration, 1)

        # Test updating to script2 keeps the same reference to the --one parameter
        # between scripts
        script = os.path.join(config.WOOEY_TEST_SCRIPTS, 'versioned_script', 'v2.py')
        with open(script) as o:
            v2 = self.storage.save(self.filename_func('v2.py'), o)

        res = utils.add_wooey_script(script_path=v2, script_name='test_versions')
        second_version = res['script']
        first_params = {i.pk for i in first_version.get_parameters()}
        second_params = {i.pk for i in second_version.get_parameters()}
        self.assertTrue(first_params.issubset(second_params))
        self.assertTrue(len(second_params), 2)

        # update to v3, drops the second param
        script = os.path.join(config.WOOEY_TEST_SCRIPTS, 'versioned_script', 'v3.py')
        with open(script) as o:
            v3 = self.storage.save(self.filename_func('v3.py'), o)

        res = utils.add_wooey_script(script_path=v3, script_name='test_versions')
        third_version = res['script']
        third_params = {i.pk for i in third_version.get_parameters()}
        self.assertEqual(first_params, third_params)


class TestFileDetectors(TestCase):
    def test_detector(self):
        self.file = os.path.join(config.WOOEY_TEST_DATA, 'fasta.fasta')
        res, preview = utils.test_fastx(self.file)
        self.assertEqual(res, True, 'Fastx parser fail')
        self.assertEqual(preview, open(self.file).readlines(), 'Fastx Preview Fail')

    def test_delimited(self):
        self.file = os.path.join(config.WOOEY_TEST_DATA, 'delimited.tsv')
        res, preview = utils.test_delimited(self.file)
        self.assertEqual(res, True, 'Delimited parser fail')
        self.assertEqual(preview, [i.strip().split('\t') for i in open(self.file).readlines()], 'Delimited Preview Fail')
