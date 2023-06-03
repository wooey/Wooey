Configuration on OpenShift
==========================

OpenShift is considerably more involved than Heroku, but allows you to freely run an app that will not sleep.

Setup OpenShift
---------------

* Setup a Django gear, this will give you a basic structure for an app.
* Clone the git repository for the app locally.

Installing Wooey
----------------

In the same local environment you cloned from, you can installed Wooey via:

::

    pip install wooey

or if you want to be on the bleeding-edge for some reason, from the github repo by:

::

    pip install git+https://github.com/wooey/Wooey.git



Bootstrapping Wooey
-------------------

Next, you want to cd into your project root, which should be called wsgi. Here, you want to run to wooey bootstrapper, which will create a full-fledged django app for you. This can be accomplished with the command:

::

    wooify -p project_name

Setup OpenShift Pt. 2
---------------------

For the rest of this guide, the wooey instance will be called wooey_openshift. Next you will want to remove the old django project, called myproject and edit the *application* file and change all instances of myproject to YourProjectName(wooey_openshift in this example).

Next, you want to setup a database and a message broker for Celery

1. Setting up a Database

    * Add a PostgreSQL instance cartridge to your app.

    * Add our database information. Openshift provides a few variables for us to use for the ip/port, but does not include one for the database name. Add that via:

      ::

        rhc env set -a YourAppName DATABASE_NAME=database_name

    * Uncomment our DATABASES variable in user_settings.py:

      ::

            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.postgresql_psycopg2',
                    # for production environments, these should be stored as environment variables
                    # I also recommend the django-heroku-postgresify package for a super simple setup
                    'NAME': os.environ.get('DATABASE_NAME', 'wooey'),
                    'USER': os.environ.get('DATABASE_USER', 'wooey'),
                    'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'wooey'),
                    'HOST': os.environ.get('DATABASE_URL', 'localhost'),
                    'PORT': os.environ.get('DATABASE_PORT', '5432')
                }
            }


    * Next, we need to change the variables since OpenShift sets up different environment variables. Rename the above variables to:

      ::

            DATABASE_USER -> OPENSHIFT_POSTGRESQL_DB_USERNAME
            DATABASE_PASSWORD -> OPENSHIFT_POSTGRESQL_DB_PASSWORD
            DATABASE_URL -> OPENSHIFT_POSTGRESQL_DB_HOST
            DATABASE_PORT -> OPENSHIFT_POSTGRESQL_DB_PORT:

2. Setting up Celery

    * Add CloudAMQP as a service, which can be done once again through the OpenShift Marketplace.

    * Update the user_settings.py file and uncomment the following:

      ::

        broker_url = os.environ.get('AMQP_URL') or \
                     os.environ.get('RABBITMQ_BIGWIG_TX_URL') or \
                     os.environ.get('CLOUDAMQP_URL', 'amqp://guest:guest@localhost:5672/')
        broker_pool_limit = 1
        worker_concurrency = 1
        task_acks_late = True
        imports = ('wooey.tasks',)

    * Change AMQP_URL to CLOUDAMQP_URI, which is the environment variable setup in your app.
    * Next, we need to tell the server to start celery. We will make a new deployment hook for this. Create the file project_root/.openshift/action_hooks/post_start with the following content:

      ::

        #!/bin/bash
        cd $OPENSHIFT_REPO_DIR
        cd wsgi
        cd YourProjectName
        rm worker1.pid
        celery multi stop worker1
        celery multi start worker1

    * To save our connections, we need to tell celery to stop when the app stops as well. Create another file, pre_stop with:

      ::

        #!/bin/bash
        cd $OPENSHIFT_REPO_DIR
        cd wsgi
        cd YourAppName
        rm worker1.pid
        celery multi stop worker1


3. Setup the requirements.txt file. The bootstrapper provides a requirements.txt file that already has all the apps needed to run Wooey. Just copy it from YourAppName/YourAppName/ to the top level directory of OpenShift (which has things like setup.py and openshiftlibs.py)

4. Edit wsgi/application and change:

    * alter myproject to YourProjectName
    * Change

      ::

        os.environ['DJANGO_SETTINGS_MODULE'] = 'myproject.settings'

      to

      ::

        os.environ['DJANGO_SETTINGS_MODULE'] = 'YourProjectName.settings'

5. Edit your git hooks to reflect the new project name:

    * There is a hidden directory at the project root, called .openshift. within it you want the directory action_hooks. cd into this, and make the following changes
    * In deploy, change myproject to YourProjectName
    * In secure_db, do the same.

6. Update where the static assets are being served from in user_settings.py (Optionally, you can follow the guide to not use OpenShift's static service and go through S3 instead :ref:`here <aws>`):

   ::

    STATIC_ROOT = os.path.join(os.environ.get('OPENSHIFT_REPO_DIR'), 'wsgi', 'static', 'static')
    MEDIA_ROOT = os.path.join(os.environ.get('OPENSHIFT_DATA_DIR'), 'user_uploads')


7. Remove DEBUG mode. In user_settings.py, add:

   ::

    DEBUG=False


Migrate your database and sync static assets
--------------------------------------------

You need to migrate your database now, setup your admin access, and sync our static files.
An easy way to do this is through the ssh command:

::

    rhc ssh -a YourAppName
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py collectstatic


Check out your app
------------------

Now, your app should be online.
