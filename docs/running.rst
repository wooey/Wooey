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

Through a Procfile
------------------

The simplest way to run Wooey is to use a Procfile with
`honcho <https://github.com/nickstenning/honcho>`__, which can be
installed via pip. Make a file, called Procfile in the root of your
project (the same place as manage.py) with the following contents:

::

    web:  python manage.py runserver
    worker: python manage.py celery worker -c 1 --beat -l info
    EOM

Your server can then be run by the simple command:

::

    honcho start

Through two separate processes
------------------------------

You can also run wooey by invoking two commands (you will need a
separate process for each):

::

    python manage.py celery worker -c 1 --beat -l info
    python manage.py runserver
