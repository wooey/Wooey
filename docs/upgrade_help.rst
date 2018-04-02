Upgrade Help
============

This document exists to help document changes between versions of Wooey and
what existing bootstrap projects may need to do to migrate to a more
recent version. The official changelog for releases is curated in
`github releases <https://github.com/wooey/Wooey/releases>`_, which will
document any major changes. Though every attempt is made to test upgrades, it
is recommended to backup your database prior to an upgrade in case your particular
usage of Wooey is not something the creators test. If an error arises, please open
an `issue <https://github.com/wooey/issues>`_ on github.

0.9.11 To 0.10
--------------

0.10 adds in support for Django 1.10 as well as Django 1.11. Django versions
prior to 1.8 are no longer officially supported.

# *Upgrading Celery*:
    Celery was upgraded to version 4.x and several changes are required:

    1) First, celery is no longer executed through

        :code: python manage.py celery

        but instead via:

        :code: celery -A your_project_name worker -l info (and any other arguments)

    2) Because `django-celery` is now deprecated and incompatible with newer Django and Celery versions,
     several settings in `settings/user_settings.py` must be updated:

    a)
        :code:
            ## Celery related options
            INSTALLED_APPS += (
                'djcelery',
                'kombu.transport.django',
            )

        must be changed to:

        :code:
            ## Celery related options
            INSTALLED_APPS += (
                'django_celery_results',
                'kombu.transport.filesystem',
            )

    b) If the default result backend was never changed, the backend must be changed from:

        :code:
            CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'

        to:

        :code:
            CELERY_RESULT_BACKEND = 'django-db'

    c) If a broker was never specified, the default broker url must be changed from

        :code:

            BROKER_URL = 'django://'

        to

        :code:
            CELERY_BROKER_URL = 'filesystem://'
            # This function exists just to ensure the filesystem has the correct folders
            def ensure_path(path):
                import errno
                try:
                    os.makedirs(path)
                except Exception as e:
                    if e.errno == errno.EEXIST:
                        pass
                    else:
                        raise
                return path

            broker_dir = ensure_path(os.path.join(BASE_DIR, '.broker'))
            CELERY_BROKER_TRANSPORT_OPTIONS = {
                "data_folder_in": ensure_path(os.path.join(broker_dir, "out")),
                "data_folder_out": ensure_path(os.path.join(broker_dir, "out")),
                "data_folder_processed": ensure_path(os.path.join(broker_dir, "processed")),
            }

    It is _highly_ recommended to not use this broker and use something such as rabbitmq or redis.

    3) The celery app instance, located in `your_project_name/wooey_celery_app.py` must be updated to:

        :code:
            from __future__ import absolute_import
            import os

            from celery import Celery


            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project_name.settings')

            app = Celery('your_project_name')

            # Using a string here means the worker will not have to
            # pickle the object when using Windows.
            app.config_from_object('django.conf:settings', namespace='CELERY')
            app.autodiscover_tasks()


            @app.task(bind=True)
            def debug_task(self):
                print('Request: {0!r}'.format(self.request))



    updated and `django-celery` replaced with `

Additional tweaks may be required for bootstrapped script's settings if a
Django upgrade is performed, such as changing `MIDDLEWARE` to `MIDDLEWARE_CLASSES`.