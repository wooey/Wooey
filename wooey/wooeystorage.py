from __future__ import absolute_import

import os

from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage


class CachedS3Boto3Storage(S3Boto3Storage):
    def __init__(self, *args, **kwargs):
        if os.environ.get("TESTING", False):
            from .tests import config

            kwargs["location"] = config.WOOEY_TEST_REMOTE_STORAGE_DIR
        super(CachedS3Boto3Storage, self).__init__(*args, **kwargs)
        self.local_storage = FileSystemStorage()

    def path(self, name):
        return self.local_storage.path(name)


class FakeRemoteStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        from .tests import config

        kwargs["location"] = config.WOOEY_TEST_REMOTE_STORAGE_PATH
        super(FakeRemoteStorage, self).__init__(*args, **kwargs)
        self.local_storage = FileSystemStorage()
