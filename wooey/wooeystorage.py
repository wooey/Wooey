from __future__ import absolute_import

import os

from boto.utils import parse_ts
from django.core.files.storage import get_storage_class, FileSystemStorage
from storages.backends.s3boto import S3BotoStorage

from . import settings as wooey_settings

# From https://github.com/jezdez/django_compressor/issues/100

class CachedS3BotoStorage(S3BotoStorage):
    def __init__(self, *args, **kwargs):
        super(CachedS3BotoStorage, self).__init__(*args, **kwargs)
        self._modified = False
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
        self._entries.pop(name, None)
        self._modified = True

    @property
    def entries(self):
        """
        Get the locally cached files for the bucket.
        """
        if self.preload_metadata and (self._modified or not self._entries):
            self._entries = dict((self._decode_name(entry.key), entry)
                                for entry in self.bucket.list(prefix=self.location))
            self._modified = True
        return self._entries


class FakeRemoteStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        from .tests.config import WOOEY_TEST_REMOTE_STORAGE
        kwargs['location'] = WOOEY_TEST_REMOTE_STORAGE
        super(FakeRemoteStorage, self).__init__(*args, **kwargs)
        self.local_storage = get_storage_class('django.core.files.storage.FileSystemStorage')()

    def path(self, name):
        return self.local_storage.path(name)
