Configuration on DigitalOcean
==========================

How to get Wooey up and running on a DO box. I followed these instructions on a Ubuntu 14.04 LTS box. For security purposes we want it to be running only on HTTPS.

Download Wooey
---------------

Download and install Wooey, by any of the standard methods. For this tutorial this was run in the home directory i.e. /home/user/

This means manage.py will be in /home/user/ProjectName

Install Nginx & uWSGI
----------------

Next we need to install Nginx, which will make setting up SSL easy and uWSGI which is how Django and Nginx talk.

There are instructions on how to install the stable branch of Nginx `here
<https://www.digitalocean.com/community/tutorials/how-to-install-the-latest-version-of-nginx-on-ubuntu-12-10>`_.

uWSGI you can install with `pip`.


Getting Wooey to listen on Port 80
-------------------

You could at this point have Wooey listen to port 80 (assuming it's open) with the following command, run from the folder containing manage.py:

::

    python manage.py runserver 0.0.0.0:80

But this leaves us wildly insecure, because all our passwords will be transmitted over HTTP. I had problems working with non-standard ports on UFW so for the purposes of this tutorial, so I set-up my ports using this `iptables linode tutorial
<https://www.linode.com/docs/security/firewalls/control-network-traffic-with-iptables>`_.


Getting Wooey to talk to Nginx & uWSGI
---------------------

We will basically follow the tutorial `here
<http://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html>`_. If you installed Wooey in a virtualenv from the get go, then follow all those steps, if not you can ignore that set:

Then we can follow the guide along with a couple changes:

1. Basic test

    * Because I was having trouble using non-standard ports, I replaced 8000 with 80 and ran the commands as root

2. Test your Django project

    * In order to get this step to work correctly I found I had to call uWSGI from the main folder where manage.py lives, in my case that was /home/user/ProjectName (I have no idea why, but otherwise it won't find the Wooey project correctly)

3. Deploying static files

    * So far I have ignored this altogether and no problems...

4. nginx and uWSGI and test.py

    * Again only got this to work on port 80 again because of non-standard port problems


Now if you want to run on a network socket, at this point you should be good to go. (Remember crucially this needs to be run from the same folder as manage.py).

::

    uwsgi --socket 127.0.0.1:8000 --wsgi-file ProjectName/wsgi.py --chmod-socket=666

If you want to use a file socket, I then created an empty file in the Wooey project directory to be used as one (in this example named django.sock).

::

    uwsgi --socket ProjectName/django.sock --wsgi-file ProjectName/test.py --chmod-socket=666


At this point we should now have Wooey running on Port 80 through Nginx.

Forcing SSL with Nginx
---------------------

I have forced SSL with the following settings. (I think I might be running two SSL redirects, one on the Nginx side and one on the Django side which is never necessary because Nginx comes first, any clarification would be welcome, however for those following along:)

I switched the main nginx block to HTTPS (there's a good tutorial `here
<https://www.digitalocean.com/community/tutorials/how-to-create-an-ssl-certificate-on-nginx-for-ubuntu-14-04>`_ if you haven't done this before).

I also added an HTTPS header to the server block listening on 443 so Django knows it's HTTPS:

::

    proxy_set_header X-Forwarded-Proto $scheme;

Then I set-up a second server block to listen on port 80 and rewrite to https:

::

    server {
        listen   80;
        listen   [::]:80;

        server_name  enter_hostname;

        return 301 https://$server_name$request_uri;
    }


Then on the Django side I added the following flags to my config in user_settings.py

::

    SECURE_SSL_REDIRECT = True #this may be the double redirect which is unnecessary.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

Finally I then added HTTP authentication, there is a good tutorial on this `here
<https://www.digitalocean.com/community/tutorials/how-to-set-up-http-authentication-with-nginx-on-ubuntu-12-10>`_. You only need to reach the first part of step 3, adding the `auth_basic` lines to your HTTPs block.

Here's an example of what my final Nginx setup file in `/etc/nginx/sites-available/django` looked like:

::

    # the upstream component nginx needs to connect to
    upstream django {
        server unix:///home/user/projectname/projectname/django.sock; # for a file socket
        #server 127.0.0.1:8000; # for a web port socket (we'll use this first)
    }

    # configuration of the server
    server {
        # the port your site will be served on
        listen      443 ssl;
        # the domain name it will serve for
        server_name server_ip; # substitute your machine's IP address or FQDN
        charset     utf-8;

        #add basic auth to prevent crawling
        auth_basic "Restricted";
        auth_basic_user_file /etc/nginx/.htpasswd;

        #get the self signed certificate
        ssl_certificate /etc/nginx/ssl/nginx.crt;
        ssl_certificate_key /etc/nginx/ssl/nginx.key;

        #add header to django knows request came through HTTPS
        proxy_set_header X-Forwarded-Proto $scheme;

        # max upload size
        client_max_body_size 75M;   # adjust to taste

        # Django media
        location /media  {
            alias /home/user/projectname/projectname/uploads;  # your Django project's media files - amend as required
        }

        location /static {
            alias /home/user/projectname/projectname/static; # your Django project's static files - amend as required
        }

        # Finally, send all non-media requests to the Django server.
        location / {
            uwsgi_pass  django;
            include     /etc/nginx/uwsgi_params;
        }
    }

    #http rewrite
    server {
        listen   80;
        listen   [::]:80;

        server_name  server_ip;

        return 301 https://$server_name$request_uri;
    }


Running Celery in the background
---------------------

All this other set-up means you then can't use honcho to run celery, because it doesn't seem to like (that's a technical term) the uWSGI command which means instead, you have to run it as a background process. This however just seems to work...

nohup celery -A your_project_name worker -c 1 --beat -l info & #you probably want to pipe this output somewhere sensible

Which means you can then run the server with the command above uwsgi command shown above.

Contributed by `dom-devel
<https://github.com/dom-devel>`_.
