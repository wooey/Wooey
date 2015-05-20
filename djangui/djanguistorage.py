from __future__ import absolute_import

from boto.utils import parse_ts
from django.core.files.storage import get_storage_class
from storages.backends.s3boto import S3BotoStorage

from . import settings as djangui_settings

# From https://github.com/jezdez/django_compressor/issues/100

class CachedS3BotoStorage(S3BotoStorage):
    def __init__(self, *args, **kwargs):
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