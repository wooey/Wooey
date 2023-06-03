Configuration on Fly.io
=======================

How to get Wooey up and running on fly.io. This assumes the `wooify` command was run with `app` as the project's name and the
fly.io project is named `wooey-test`.

Directory Layout
----------------

::

    app
    ├── app
    │   ├── application files
    ├── manage.py # this is unused and can be removed if running via django-admin
    ├── fly.toml
    ├── Dockerfile
    ├── requirements.txt

Fly TOML file
-------------

Here is an example fly.toml file. One arbitary choice is the webserver used. Here, waitress is used but there are many alternatives such as
gunicorn and uwsgi.

::

    app = "wooey-test"
    kill_signal = "SIGINT"
    kill_timeout = 5

    [env]
    DJANGO_SETTINGS_MODULE = "app.settings"

    [experimental]
    allowed_public_ports = []
    auto_rollback = true

    [build]
    dockerfile = "Dockerfile"

    [deploy]
    release_command = "django-admin migrate"

    [processes]
    web = "waitress-serve --connection-limit 2000 --channel-timeout=300 --port=8080 app.wsgi:application"
    worker = "celery -A app worker -c 1 --beat -l info --without-gossip --without-mingle --without-heartbeat"

    [[services]]
    http_checks = []
    internal_port = 8080
    processes = ["web"]
    protocol = "tcp"
    script_checks = []
    [services.concurrency]
        hard_limit = 25
        soft_limit = 20
        type = "connections"

    [[services.ports]]
        force_https = true
        handlers = ["http"]
        port = 80

    [[services.ports]]
        handlers = ["tls", "http"]
        port = 443

    [[services.tcp_checks]]
        grace_period = "1s"
        interval = "15s"
        restart_limit = 0
        timeout = "2s"

Dockerfile
----------

Here is an example Dockerfile

::

    FROM python:3.10.9-slim-buster

    ENV VIRTUAL_ENV=/opt/venv

    RUN useradd -u 1000 wooey
    RUN mkdir -p $VIRTUAL_ENV && chown wooey:wooey $VIRTUAL_ENV
    USER wooey

    RUN python3 -m venv --system-site-packages $VIRTUAL_ENV
    ENV PATH="$VIRTUAL_ENV/bin:$PATH"

    COPY --chown=wooey:wooey requirements.txt requirements.txt
    RUN pip install -r requirements.txt

    COPY --chown=wooey:wooey app app
    ENV PYTHONPATH="/app:$PYTHONPATH"


Requirements
------------

Here is an example requirements.txt

::

    Django~=3.2.14
    wooey==0.13.2
    django-storages==1.13.2
    django-autoslug==1.9.8
    dj-database-url==1.0.0
    boto3==1.26.27
    waitress==2.1.2
    collectfast==2.2.0
    psycopg2-binary==2.9.5
