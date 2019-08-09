from django.core.management.base import BaseCommand
import logging

from ...models import WooeyJob
from ... import settings as wooey_settings

LOG = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check kubernetes job statuses and refresh logs'

    def handle(self, *args, **options):
        if wooey_settings.WOOEY_KUBERNETES:
            unfinished_jobs = WooeyJob.objects.filter(
                kubernetes_pod_name__isnull=False,
                status__in=[WooeyJob.SUBMITTED, WooeyJob.RUNNING]
            )

            for job in unfinished_jobs:
                LOG.info(f"Check status of job with id `{job.id}`")
                job.check_kubernetes_pod()
