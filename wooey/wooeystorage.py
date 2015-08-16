from __future__ import absolute_import

import os

from boto.utils import parse_ts
from django.core.files.storage import get_storage_class, FileSystemStorage
from storages.backends.s3boto import S3BotoStorage

from . import settings as wooey_settings

# From https://github.com/jezdez/django_compressor/issues/100

class CachedS3BotoStorage(S3BotoStorage):
    def __init__(self, *args, **kwargs):
        if os.environ.get('TESTING', False):
            from .tests import config
            kwargs['location'] = config.WOOEY_TEST_REMOTE_STORAGE_DIR
        super(CachedS3BotoStorage, self).__init__(*args, **kwargs)
        self.local_storage = get_storage_class('django.core.files.storage.FileSystemStorage')()

    def _open(self, name, mode='rb'):
        original_file = super(CachedS3BotoStorage, self)._open(name, mode=mode)
        if name.endswith('.gz'):
            return original_file
        return original_file

    def modified_time(self, name):
        name = self._normalize_name(self._clean_name(name))
        entry = self.entries.get(name)
        if entry is None:
            entry = self.bucket.get_key(self._encode_name(name))
        # Parse the last_modified string to a local datetime object.
        return parse_ts(entry.last_modified)

    def path(self, name):
        return self.local_storage.path(name)

    def delete(self, name):
        # we have to remove the name from the _entries cache or else deleted files will persist in our cache
        # and give false information
        super(CachedS3BotoStorage, self).delete(name)
        name = self._normalize_name(self._clean_name(name))
        encoded_name = self._encode_name(name)
        self._entries.pop(encoded_name, None)


class FakeRemoteStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        from .tests import config
        kwargs['location'] = config.WOOEY_TEST_REMOTE_STORAGE_PATH
        super(FakeRemoteStorage, self).__init__(*args, **kwargs)
        self.local_storage = get_storage_class('django.core.files.storage.FileSystemStorage')()
