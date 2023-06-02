.. _celery_guide:

Wooey Celery Configuration
==========================

Celery
------

`Celery
<https://celery.readthedocs.org/en/stable/>`_ is an app designed to distribute tasks to workers. This is generally useful as a way to scale up a server and carry out work without
impacting the main webserver.

The Broker
----------

In celery, the broker exists to pass messages between servers. There are several brokers to use, with RabbitMQ and Redis being the common choices.
Here, we detail how to use RabbitMQ (AMQP).

If you are coming from a bootstrapped project, to switch to an AMQP broker, it is a matter of uncommenting the following lines in your production settings.
In the code, there are 2 cloud rabbit providers we have used in the past for our demo application.

::

    broker_url = os.environ.get('AMQP_URL') or \
                 os.environ.get('RABBITMQ_BIGWIG_TX_URL') or \
                 os.environ.get('CLOUDAMQP_URL', 'amqp://guest:guest@localhost:5672/')
    broker_pool_limit = 1
    worker_concurrency = 1
    task_acks_late = True

If you are coming from a project which has wooey installed as an additional app, you want to add the above to your settings.

Additional Heroku Options
-------------------------

For heroku, you will want to add AMQP to your app through the dashboard, which should give you a AMQP url compatible with the above options.

Fly.dev Setup
-------------

For fly.dev, we use the `Cloudamqp service <https://www.cloudamqp.com/>`_, whose free tier is sufficient for our needs.
