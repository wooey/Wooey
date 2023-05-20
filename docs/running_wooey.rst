Running Wooey
=============

Wooey depends on a distributed worker to handle tasks, you can disable
this by setting **WOOEY\_CELERY** to False in your settings, which will
allow you to run Wooey through the simple command:

::

    python manage.py runserver

However, this will cause the server to execute tasks, which will block
the site.

The recommended ways to run Wooey are:

Through two separate processes
------------------------------

You can run Wooey by calling two commands (you will need a
separate process for each):

::

    celery -A your_project_name worker -c 1 --beat -l info
    python manage.py runserver

On Windows, the ``--beat`` option may not be supported and the `eventlet`
pool will need to be specified. This looks like:

::

    celery -A your_project_name worker --pool=eventlet -l info

Through a Procfile
------------------

A simple way to run Wooey on a server such as Heroku is through a Procfile
using `honcho <https://github.com/nickstenning/honcho>`__, which can be
installed via pip. Make a file, called Procfile in the root of your
project (the same place as manage.py) with the following contents:

::

    web:  python manage.py runserver
    worker: celery -A your_project_name worker -c 1 --beat -l info
    EOM

Your server can then be run by the simple command:

::

    honcho start

On Windows, the ``--beat`` option may not be supported.


With Docker
-----------

`Docker <https://www.docker.com>`__ is a great way to get Wooey up and running quickly, especially
for development. To get Wooey up and running with Docker and `docker-compose <https://docs.docker.com/compose/>`__,
follow these commands:

::

    git clone git@github.com:wooey/Wooey.git
    cd Wooey/docker
    ./wooey-compose build wooey
    ./wooey-compose run wooey python manage.py createsuperuser
    ... fill in info ...
    ./wooey-compose up wooey celery

Now, a local Wooey server will be available at http://localhost:8081/ (or change the port in
docker-compose.override.yml).
