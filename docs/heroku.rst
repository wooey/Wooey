Configuration on Heroku
=======================

Installing Wooey
----------------

Wooey can be installed by the simple command:

::

    pip install wooey

or if you want to be on the bleeding-edge for some reason, from the github repo by:

::

    pip install git+https://github.com/wooey/Wooey.git

Bootstrapping Wooey
-------------------

The wooey project can be boostraped, which will create a full-fledged django app for you. This can be accomplished with the command:

::

    wooify -p project_name


For the rest of this guide, the wooey instance will be called wooey_heroku.

Setup Heroku and git
--------------------

Of course, you will at this point need to have an app on Heroku.

* Create an app on Heroku
* Login to heroku on the command line

Next, setup git:

* cd woeey_heroku
* git init
* heroku git:remote -a wooey

Setup dependencies
------------------

For the bootstrapping, we have included a requirements file to assist in getting newer users up and running. This can be found here:

::

    wooey_heroku/wooey_heroku/requirements.txt

We want to add one more dependency to this, which we will use momentarily. To the bottom of this, add:

::

    django-heroku-postgresify

You will want to move this file to the same location as manage.py

Setup a Procfile
----------------

Create a file, called Procfile, which tells Heroku how to run your app, with the following contents:

::

    web: waitress-serve --connection-limit 2000 --channel-timeout=300 --port=$PORT wooey_heroku.wsgi:application
    worker: python manage.py celery worker -c 1 --beat -l info

Setup Environment Vars on Heroku

You will need to add a few settings to your heroku config at this point to tell Heroku where to find your Django settings. This can be done by the command line or through the settings gui.

::

    heroku config:set -a wooey DJANGO_SETTINGS_MODULE=wooey_heroku.settings

Production Settings
-------------------

At this point, your wooey app is insecure -- so we will edit your settings to fix this as well as make it more production-ready by changing our database.


You will want to edit user_settings.py, which is found in wooey_heroku/wooey_heroku/settings/user_settings.py

In here, there are comments indicating what each variable means. You will want to change the DATABASES variable to:

::

    DATABASES = postgresify()

and add the following import:

::

    from postgresify import postgresify

Storage
-------

Heroku uses an ephemeral file system, so you will need to create your own persistent storage. Amazon S3 services is a natural place for this.
To start, complete these steps:

* Create a bucket
* Setup an IAM user/group with full access to S3 buckets:
* Copy down your access key ID and secret access key id
* Add the user to your IAM group that has control of S3 buckets.
* Set these variables in heroku:
  ::

      heroku config:set -a wooey AWS_ACCESS_KEY_ID=access_key
      heroku config:set -a wooey AWS_SECRET_ACCESS_KEY=secret_key
      heroku config:set -a wooey AWS_STORAGE_BUCKET_NAME=bucket_name

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
            <AllowedOrigin>wooey.herokuapp.com</AllowedOrigin>
            <AllowedMethod>GET</AllowedMethod>
            <AllowedMethod>POST</AllowedMethod>
            <AllowedMethod>PUT</AllowedMethod>
            <AllowedHeader>*</AllowedHeader>
        </CORSRule>
    </CORSConfiguration>

* Update our user_settings.py and uncomment out the following section:

  ::

        from boto.s3.connection import VHostCallingFormat


        INSTALLED_APPS += (
            'storages',
            'collectfast',
        )


        # We have user authentication -- we need to use https (django-sslify)if not DEBUG:
            MIDDLEWARE_CLASSES = ['sslify.middleware.SSLifyMiddleware']+list(MIDDLEWARE_CLASSES)
            SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


        ALLOWED_HOSTS = (
            'localhost',
            '127.0.0.1',
            "wooey.herokuapp.com",# put your site here)


        AWS_CALLING_FORMAT = VHostCallingFormat


        AWS_ACCESS_KEY_ID = environ.get('AWS_ACCESS_KEY_ID', '')
        AWS_SECRET_ACCESS_KEY = environ.get('AWS_SECRET_ACCESS_KEY', '')
        AWS_STORAGE_BUCKET_NAME = environ.get('AWS_STORAGE_BUCKET_NAME', '')
        AWS_AUTO_CREATE_BUCKET = True
        AWS_QUERYSTRING_AUTH = FalseAWS_S3_SECURE_URLS = True
        AWS_FILE_OVERWRITE = FalseAWS_PRELOAD_METADATA = True
        AWS_S3_CUSTOM_DOMAIN = environ.get('AWS_S3_CUSTOM_DOMAIN', '')


        GZIP_CONTENT_TYPES = (
            'text/css',
            'application/javascript',
            'application/x-javascript',
            'text/javascript',
        )


        AWS_EXPIREY = 60 * 60 * 7AWS_HEADERS = {
            'Cache-Control': 'max-age=%d, s-maxage=%d, must-revalidate' % (AWS_EXPIREY,
                AWS_EXPIREY)
        }


        STATIC_URL = 'http://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
        MEDIA_URL = '/user-uploads/'
        STATICFILES_STORAGE = DEFAULT_FILE_STORAGE = 'wooey.wooeystorage.CachedS3BotoStorage'WOOEY_EPHEMERAL_FILES = True

In the above step, make sure you change wooey.herokuapp.com to your app.

Celery
------

The last bit to setup is celery. For this, we will use the free AMPQ services from heroku, such as RabbitMQ Bigwig. After enabling this in your heroku dashboard, you can uncomment the following lines:

::

    CELERY_RESULT_BACKEND = 'amqp'BROKER_URL = os.environ.get('AMQP_URL') or \
                 os.environ.get('RABBITMQ_BIGWIG_TX_URL') or \
                 os.environ.get('CLOUDAMQP_URL', 'amqp://guest:guest@localhost:5672/')
    BROKER_POOL_LIMIT = 1
    CELERYD_CONCURRENCY = 1
    CELERY_TASK_SERIALIZER = 'json'
    ACKS_LATE = True


Finally, you want to disable the DEBUG setting by adding

::

    DEBUG = False

Add everything to git and push it upstream

::

    git add .
    git commit -m 'initial commit'
    git push -u heroku master

At the last step, the -u indicates to create the branch master if it does not exist on the remote.

Migrate your database and sync static assets
--------------------------------------------

You need to migrate your database now, setup your admin access, and put our static files on the S3 server.
An easy way to do this is through heroku:

::

    heroku run -a wooey bash
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py collectstatic


Check out your app
------------------

Now, your app should be online. You can check it at <appname>.herokuapp.com.

