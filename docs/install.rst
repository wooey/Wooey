Installation
============

::

    pip install wooey

Currently, Wooey supports Django versions 1.8+. To use Wooey in a project which is still running Django 1.6 or 1.7, you must install
version 0.9.8.

A Wooey only project
--------------------

There is a bootstrapper included with wooey, which will create a Django
project and setup most of the needed settings automagically for you.

::

    1. wooify -p ProjectName
    2. Follow the instructions at the end of the bootstrapper
       to create the admin user and access the admin page
    3. Login to the admin page wherever the project is
       being hosted (locally this would be localhost:8000/admin)

Installation with existing Django Projects
------------------------------------------

::

    1. Add 'wooey' to INSTALLED_APPS in settings.py (and optionally, djcelery unless you wish to tie into an existing celery instance)
    2. Add the following to your urls.py:
       path(r'', include('wooey.urls')),
       (Note: it does not need to be rooted at your site base,
        you can have r'wooey/'... as your router):

    3. Migrate your database:
        # Django 1.8 and above
        ./manage.py makemigrations
        ./manage.py migrate

    4. Ensure the following are in your TEMPLATE_CONTEXT_PROCSSORS variable:
        TEMPLATE_CONTEXT_PROCESSORS = [
        ...
        'django.contrib.auth.context_processors.auth',
        'django.core.context_processors.request'
        ...]

    5. If necessary, setup static file serving. For non-production servers, Django
       can be setup to do this for you by adding the following to your urls.py:

        from django.conf import settings
        from django.conf.urls.static import static
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    6. You may also need to define a MEDIA_ROOT, MEDIA_URL, STATIC_ROOT, and STATIC_URL
       if these are not setup already.

Installation on remote servers
------------------------------

We have provided guides for several available services that host sites, as well as guides for steps common to multiple services (such as using Amazon Web Services).
For examples not listed here, you are free to open up an `issue <https://github.com/wooey/wooey/issues>`_. (or document it and send a pull request!).


.. toctree::
   :maxdepth: 1

   heroku
   digitalocean
   openshift
   fly
   aws
   celery
