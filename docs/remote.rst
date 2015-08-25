Remote File Systems
===================

Wooey has been tested on heroku with S3 as a file storage system.
Settings for this can be seen in the user\_settings.py, which give you a
starting point for a non-local server. In short, you need to change your
storage settings like such:

STATICFILES\_STORAGE = DEFAULT\_FILE\_STORAGE =
'wooey.wooeystorage.CachedS3BotoStorage' WOOEY\_EPHEMERAL\_FILES = True
