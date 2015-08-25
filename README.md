![Wooey!](wooey-banner.png)

Wooey is a simple web interface to run command line Python scripts. Think of it as an easy way to get your scripts up on the web for routine data analysis, file processing, or anything else.


[![Build Status](https://travis-ci.org/wooey/Wooey.svg?branch=master)](https://travis-ci.org/wooey/Wooey)
[![Coverage Status](https://coveralls.io/repos/wooey/Wooey/badge.svg?branch=master)](https://coveralls.io/r/wooey/Wooey?branch=master)
[![Join the chat at https://gitter.im/wooey/Wooey](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/wooey/Wooey?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

1. [Installation](#install)
    1. [A Wooey Only Project](#djonly)
    2. [Adding Wooey to Existing Projects](#existing)
2. [Running Wooey](#running)
    1. [A Procfile](#procfile)
    2. [Two processes](#two-procs)
3. [Adding Scripts](#adding)
4. [Script Organization](#organization)
5. [Script Permissions](#permissions)
6. [Configuration](#config)
7. [Usage with S3/remote file systems](#s3)
8. [Script Guidelines](#script-guide)

 
The project was inspired by how simply and powerfully [sandman](https://github.com/jeffknupp/sandman) 
could expose users to a database and by how [Gooey](https://github.com/chriskiehl/Gooey) turns 
ArgumentParser-based command-line scripts into WxWidgets GUIs. Originally two separate
projects (Django-based djangui by [Chris Mitchell](https://github.com/Chris7) and Flask-based Wooey by [Martin Fitzpatrick](https://github/mfitzp)) it has been merged to combine our efforts.


Both of our tools were based on our needs as data scientists to have a system that could:
    
    1. Autodocument workflows for data analysis
        (simple model saving).
    2. Enable fellow lab members with no command line
        experience to utilize python scripts.
    3. Enable the easy wrapping of any program in simple
       python instead of having to use language specific 
       to existing tools such as Galaxy.

# <a name="install"></a>Installation

    pip install wooey
    
## <a name="djonly"></a>A Wooey only project

There is a bootstrapper included with wooey, which will create a Django project and setup most of the needed settings automagically for you.

    1. wooify -p ProjectName
    2. Follow the instructions at the end of the bootstrapper
       to create the admin user and access the admin page
    3. Login to the admin page wherever the project is
       being hosted (locally this would be localhost:8000/admin)
    
## <a name="existing"></a>Installation with existing Django Projects

    1. Add 'wooey' to INSTALLED_APPS in settings.py (and optionally, djcelery unless you wish to tie into an existing celery instance)
    2. Add the following to your urls.py:
       url(r'^', include('wooey.urls')),
       (Note: it does not need to be rooted at your site base,
        you can have r'^wooey/'... as your router):
       
    3. Migrate your database:
        # Django 1.6 and below:
        ./manage.py syncdb
        
        # Django 1.7 and above
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

# <a name="running"></a>Running Wooey

Wooey depends on a distributed worker to handle tasks, there are a number of recommended ways to run them together:

## <a name="procfile"></a>Through a Procfile

The simplest way to run Wooey is to use a Procfile with [honcho](https://github.com/nickstenning/honcho), which can be installed via pip. Make a file, called Procfile in the root of your project (the same place as manage.py) with the following contents:

```
web:  python manage.py runserver
worker: python manage.py celery worker -c 1 --beat -l info
EOM
```

Your server can then be run by the simple command:
```
honcho start
```

## <a name="two-procs"></a>Through two separate processes

You can also run wooey by invoking two commands (you will need a separate process for each, for example running
in a separate terminal):

```
python manage.py celery worker -c 1 --beat -l info
python manage.py runserver
```

## <a name="single-process"></a>Single process

To run Wooey in a single process you can set **WOOEY_CELERY** to False in your settings.
This will bypass the distributed task server and allow you to run Wooey through the simple command:

```
python manage.py runserver
```

However, this will cause the server to execute tasks. This will block the site and is not recommended.

        
# <a name="adding"></a>Adding & Managing Scripts

Scripts may be added in two ways, through the Django admin interface as well as through the *addscript* command in manage.py.

### The admin Interface

Within the django admin interface, scripts may be added to through the 'scripts' model. Here, the user permissions may be set, as
well as cosmetic features such as the script's display name, description (if provided, otherwise the script name and description
will be automatically populated by the description from argparse if available).
 
### The command line

`./manage.py addscript`

This will add a script or a folder of scripts to Wooey (if a folder is passed instead of a file).
 By default, scripts will be created in the 'Wooey Scripts' group.
 
# <a name="organization"></a>Script Organization
 
Scripts can be viewed at the root url of Wooey. The ordering of scripts, and groupings of scripts can be altered by
changing the 'Script order' or 'Group order' options within the admin.

# <a name="permissions"></a>Script Permissions
 
Scripts and script groups can be relegated to certain groups of users. The 'user groups' option, if set, will restrict script usage
to users within selected groups. 

Scripts and groups may also be shutoff to all users by unchecked the 'script/group active' option.
       
# <a name="config"></a>Configuration

**WOOEY_FILE_DIR**: String, where the files uploaded by the user will be saved (Default: wooey_files)

**WOOEY_CELERY**: Boolean, whether or not celery is enabled. If disabled, tasks will run locally and block execution. (Default: True)

**WOOEY_CELERY_TASKS**: String, the name of the celery tasks for Wooey. (Default: 'wooey.tasks')

**WOOEY_ALLOW_ANONYMOUS**: Boolean, whether to allow submission of jobs by anonymous users. (Default: True)

By default, Wooey has a basic user account system. It is very basic, and doesn't confirm registrations via email.

**WOOEY_AUTH**: Boolean, whether to use the authorization system of Wooey for simple login/registration. (Default: True)

**WOOEY_LOGIN_URL**: String, if you have an existing authorization system, the login url: (Default: settings.LOGIN_URL

**WOOEY_REGISTER_URL**: String, if you have an existing authorization system, the registration url: (Default: /accounts/register/)

**WOOEY_EPHEMERAL_FILES**: Boolean, if your file system changes with each restart. (Default: False)

**WOOEY_SHOW_LOCKED_SCRIPTS**: Boolean, whether to show locked scripts as disabled or hide them entirely. (Defalt: True -- show as disabled)

# <a name="s3"></a>Remote File Systems

Wooey has been tested on heroku with S3 as a file storage system. Settings for this can be seen in the user_settings.py, which give you a starting point for a non-local server. In short, you need to change your storage settings like such:

<code>

STATICFILES_STORAGE = DEFAULT_FILE_STORAGE = 'wooey.wooeystorage.CachedS3BotoStorage'
WOOEY_EPHEMERAL_FILES = True

</code>

# <a name="script-guide"></a>Script Guidelines

The easiest way to make your scripts compatible with Wooey is to define your ArgParse class in the global scope. For instance:

```

import argparse
import sys

parser = argparse.ArgumentParser(description="https://projecteuler.net/problem=1 -- Find the sum of all the multiples of 3 or 5 below a number.")
parser.add_argument('--below', help='The number to find the sum of multiples below.', type=int, default=1000)

def main():
    args = parser.parse_args()
    ...

if __name__ == "__main__":
    sys.exit(main())

```

If you have failing scripts, please open an issue with their contents so we can handle cases as they appear and try to make this as all-encompasing as possible. One known area which fails currently is defining your argparse instance inside the `if __name__ == "__main__" block`
