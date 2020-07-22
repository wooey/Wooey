.. _celery_guide:

Wooey Celery Configuration
==========================

Celery
------

`Celery
<https://celery.readthedocs.org/en/stable/>`_ is an app designed to pass messages. This has broad implications, such as the ability to have a distributed setup where
workers perform the work, with a central node delegating the tasks (without halting the server to perform these tasks).

The backend
-----------

There are several backends to use, here we can use a database backend or a server as a backend. By default, Wooey uses the database as a backend. If you wish to move to a more robust system,
there are several options such as AMQP or redis. Here, we detail how to use AMQP.

If you are coming from a bootstrapped project, to switch to an AMQP backend, it is a matter of uncommenting the following lines in your production settings:

::

    CELERY_RESULT_BACKEND = 'amqp'BROKER_URL = os.environ.get('AMQP_URL') or \
                 os.environ.get('RABBITMQ_BIGWIG_TX_URL') or \
                 os.environ.get('CLOUDAMQP_URL', 'amqp://guest:guest@localhost:5672/')
    BROKER_POOL_LIMIT = 1
    CELERYD_CONCURRENCY = 1
    CELERY_TASK_SERIALIZER = 'json'
    ACKS_LATE = True

If you are coming from a project which has wooey installed as an additional app, you want to add the above to your settings.

Additional Heroku Options
-------------------------

For heroku, you will want to add AMQP to your app through the dashboard, which should give you a AMQP url compatible with the above options.
