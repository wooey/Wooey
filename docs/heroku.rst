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
    worker: celery -A your_project_name worker -c 1 --beat -l info

Setup Environment Vars on Heroku

You will need to add a few settings to your heroku config at this point to tell Heroku where to find your Django settings. This can be done by the command line or through the settings gui.

::

    heroku config:set -a wooey DJANGO_SETTINGS_MODULE=wooey_heroku.settings

Storage
-------

Heroku uses an ephemeral file system, so you will need to create your own persistent storage. Amazon S3 services is a natural place for this.
To start, complete the steps found :ref:`here <aws>`.

Celery
------

The last bit to setup is celery. For this, we will use the free AMQP services from heroku, such as RabbitMQ Bigwig. After enabling this in your heroku dashboard, complete the guide found :ref:`here <celery_guide>`.

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
