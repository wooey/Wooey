.. _aws:

Configuring Amazon S3 Storage for Wooey
=======================================

Prerequisites
-------------

Before getting started, this guide assumes you have several things setup:

* An AWS account
* An S3 Bucket
* An IAM user/group with full access to the S3 bucket (remember to add your user to the IAM group controlling the bucket!)
* Are using a storage app in Django. We recommend `django-storages <https://github.com/jschneier/django-storages>`_.


Steps to Follow
---------------

* Edit your CORS configuration for the bucket:
  ::

    <?xml version="1.0" encoding="UTF-8"?>
    <CORSConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
        <CORSRule>
            <AllowedOrigin>*</AllowedOrigin>
            <AllowedMethod>GET</AllowedMethod>
            <MaxAgeSeconds>3000</MaxAgeSeconds>
            <AllowedHeader>Authorization</AllowedHeader>
        </CORSRule>
        <CORSRule>
            <AllowedOrigin>wooey.fly.dev</AllowedOrigin>
            <AllowedMethod>GET</AllowedMethod>
            <AllowedMethod>POST</AllowedMethod>
            <AllowedMethod>PUT</AllowedMethod>
            <AllowedHeader>*</AllowedHeader>
        </CORSRule>
    </CORSConfiguration>

* If using a bootstrapped Wooey, update user_settings.py and uncomment out the following section: (or add it for apps Wooey was added to)

  ::

        from boto.s3.connection import VHostCallingFormat


        INSTALLED_APPS += (
            'storages',
            'collectfast',
        )


        # We have user authentication -- we need to use https (django-sslify)
        if not DEBUG:
            MIDDLEWARE = ['sslify.middleware.SSLifyMiddleware'] + list(MIDDLEWARE)
            SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


        ALLOWED_HOSTS = (
            'localhost',
            '127.0.0.1',
            "wooey.fly.dev",  # put your site here
        )


        AWS_CALLING_FORMAT = VHostCallingFormat


        AWS_ACCESS_KEY_ID = environ.get('AWS_ACCESS_KEY_ID', '')
        AWS_SECRET_ACCESS_KEY = environ.get('AWS_SECRET_ACCESS_KEY', '')
        AWS_STORAGE_BUCKET_NAME = environ.get('AWS_STORAGE_BUCKET_NAME', '')
        AWS_AUTO_CREATE_BUCKET = True
        AWS_QUERYSTRING_AUTH = True
        AWS_S3_SECURE_URLS = True
        AWS_FILE_OVERWRITE = False
        AWS_PRELOAD_METADATA = True
        AWS_S3_CUSTOM_DOMAIN = environ.get('AWS_S3_CUSTOM_DOMAIN', '')


        GZIP_CONTENT_TYPES = (
            'text/css',
            'application/javascript',
            'application/x-javascript',
            'text/javascript',
        )


        AWS_EXPIREY = 60 * 60 * 7
        AWS_HEADERS = {
            'Cache-Control': 'max-age=%d, s-maxage=%d, must-revalidate' % (AWS_EXPIREY,
                AWS_EXPIREY)
        }


        STATIC_URL = 'http://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
        MEDIA_URL = '/user-uploads/'
        STATICFILES_STORAGE = DEFAULT_FILE_STORAGE = 'wooey.wooeystorage.CachedS3BotoStorage'
        WOOEY_EPHEMERAL_FILES = True

In the above step, make sure you change wooey.fly.dev to your app's address.

Configuration Settings
----------------------

Next, as part of any good app -- you should be storing your secret information in environmental
variables instead of hard-coding them into the app. You will want to set these variables::

    AWS_ACCESS_KEY_ID=access_key
    AWS_SECRET_ACCESS_KEY=secret_key
    AWS_STORAGE_BUCKET_NAME=bucket_name

If you are using Heroku, you can set them as follows::

    heroku config:set -a wooey AWS_ACCESS_KEY_ID=access_key
    heroku config:set -a wooey AWS_SECRET_ACCESS_KEY=secret_key
    heroku config:set -a wooey AWS_STORAGE_BUCKET_NAME=bucket_name

For fly.dev (which we now use to host) ::

    flyctl secrets set KEY=value
