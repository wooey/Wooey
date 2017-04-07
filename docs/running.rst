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

    python manage.py celery worker -c 1 --beat -l info
    python manage.py runserver

On Windows, the ``--beat`` option may not be supported.

Through a Procfile
------------------

The recommended way to run Wooey is to use a Procfile with
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
    
On Windows, the ``--beat`` option may not be supported.


Production installation of Wooey utilizing NGINX and uWSGI
----------------------------------------------------------

1. add a domain name to ALLOWED_HOSTS in django_settings.py in the settings dir of your project
2. specify a static dir you like in STATIC_ROOT- default is OK
3. make sure the entire directory tree is chmodded and chgrouped appropriately for the webserver user..sqlite db needs to be writable by them, etc.
4. 


sample nginx config

::
    server {
        listen 80;
        server_name <YOUR_DOMAIN>;
        root /PATH/TO/MANAGE.PY;
        location = /favicon.ico { access_log off; log_not_found off; }
        location /static/ { #get dat NGINX to serve the easy stuff, have a rest uWSGI
        root /PATH/TO/WHEREVER/YOU/PUT/STATIC;
    }
    location / {
        include uwsgi_params;
        uwsgi_pass unix:/PATH/TO/[socket_name from uwsgi conf];
        uwsgi_read_timeout 300;
    }
    }

sample uwsgi config

::
  
   [uwsgi]
   # variables
   plugin = </path/to/your/built/uwsgi/python/plugin> #may just need to say "python", depending how you've installed uwsgi
   projectname = <YOURPROJECT>
   base = </PATH/TO/ONE/DIR/ABOVE/MANAGE.PY>
   chdir = %(base)/%(projectname)
   module = %(projectname).wsgi:application

   # config
   harakiri = 240
   master = true
   protocol = uwsgi
   env = DJANGO_SETTINGS_MODULE=%(projectname).settings
   pythonpath = %(base)/src/%(projectname)
   module = %(projectname).wsgi
    socket = </you/pick/path/to/socket>
    chmod-socket = 666
    logto = </somewhere/the/webserver/can/write>
    attach-daemon = python manage.py celery worker -c 1 --beat -l info
  



