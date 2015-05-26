# Djangui

1. [Installation](#install)
    1. [A Djangui Only Project](#djonly)
    2. [Adding Djangui to Existing Projects](#existing)
2. [Running Djangui](#running)
    1. [A Procfile](#procfile)
    2. [Two processes](#two-procs)
3. [Adding Scripts](#adding)
4. [Script Organization](#organization)
5. [Script Permissions](#permissions)
6. [Configuration](#config)
7. [Usage with S3/remote file systems](#s3)

Djangui is designed to take scripts implemented with a python command line argument parser (such as argparse), and convert them into a web interface.
 
This project was inspired by how simply and powerfully [sandman](https://github.com/jeffknupp/sandman) could expose users to a database. 
It was also based on my own needs as a data scientist to have a system that could:
    
    1. Autodocument my workflows for data analysis
        (simple model saving).
    2. Enable fellow lab members with no command line
        experience to utilize python scripts.
    3. Enable the easy wrapping of any program in simple
       python instead of having to use language specific 
       to existing tools such as Galaxy.

# <a name="install"></a>Installation

    pip install django-djangui
    
## <a name="djonly"></a>A Djangui only project

There is a bootstrapper included with djangui, which will create a Django project and setup most of the needed settings automagically for you.

    1. djanguify.py -p ProjectName
    2. Follow the instructions at the end of the bootstrapper
       to create the admin user and access the admin page
    3. Login to the admin page wherever the project is
       being hosted (locally this would be localhost:8000/admin)
    
## <a name="existing"></a>Installation with existing Django Projects

    1. Add 'djangui' to INSTALLED_APPS in settings.py
    2. Add the following to your urls.py:
       `url(r'^', include('djangui.urls')),`
       (Note: it does not need to be rooted at your site base,
        you can have r'^djangui/'... as your router):
       
    3. Migrate your database:
        # Django 1.6 and below:
        `./manage.py syncdb`
        
        # Django 1.7 and above
        `./manage.py makemigrations`
        `./manage.py migrate`

# <a name="running"></a>Running Djangui

Djangui depends on a distributed worker to handle tasks, you can disable this by setting **DJANGUI_CELERY** to False in your settings, which will allow you to run Djangui through the simple command:

```
python manage.py runserver
```

However, this will cause the server to execute tasks, which will block the site.

The recommended ways to run Djangui are:

## <a name="procfile"></a>Through a Procfile

The simplest way to run Djangui is to use a Procfile with [honcho](https://github.com/nickstenning/honcho), which can be installed via pip. Make a file, called Procfile in the root of your project (the same place as manage.py) with the following contents:

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

You can also run djangui by invoking two commands (you will need a separate process for each):

```
python manage.py celery worker -c 1 --beat -l info
python manage.py runserver
```

        
# <a name="adding"></a>Adding & Managing Scripts

Scripts may be added in two ways, through the Django admin interface as well as through the *addscript* command in manage.py.

### The admin Interface

Within the django admin interface, scripts may be added to through the 'scripts' model. Here, the user permissions may be set, as
well as cosmetic features such as the script's display name, description (if provided, otherwise the script name and description
will be automatically populated by the description from argparse if available).
 
### The command line

`./manage.py addscript`

This will add a script or a folder of scripts to Djangui (if a folder is passed instead of a file).
 By default, scripts will be created in the 'Djangui Scripts' group.
 
# <a name="organization"></a>Script Organization
 
Scripts can be viewed at the root url of Djangui. The ordering of scripts, and groupings of scripts can be altered by
changing the 'Script order' or 'Group order' options within the admin.

# <a name="permissions"></a>Script Permissions
 
Scripts and script groups can be relegated to certain groups of users. The 'user groups' option, if set, will restrict script usage
to users within selected groups. 

Scripts and groups may also be shutoff to all users by unchecked the 'script/group active' option.
       
# <a name="config"></a>Configuration

**DJANGUI_FILE_DIR**: String, where the files uploaded by the user will be saved (Default: djangui_files)

**DJANGUI_CELERY**: Boolean, whether or not celery is enabled. If disabled, tasks will run locally and block execution. (Default: True)

**DJANGUI_CELERY_TASKS**: String, the name of the celery tasks for Djangui. (Default: 'djangui.tasks')

**DJANGUI_ALLOW_ANONYMOUS**: Boolean, whether to allow submission of jobs by anonymous users. (Default: True)

By default, Djangui has a basic user account system. It is very basic, and doesn't confirm registrations via email.

**DJANGUI_AUTH**: Boolean, whether to use the authorization system of Djangui for simple login/registration. (Default: True)

**DJANGUI_LOGIN_URL**: String, if you have an existing authorization system, the login url: (Default: settings.LOGIN_URL

**DJANGUI_REGISTER_URL**: String, if you have an existing authorization system, the registration url: (Default: /accounts/register/)

**DJANGUI_EPHEMERAL_FILES**: Boolean, if your file system changes with each restart. (Default: False)

**DJANGUI_SHOW_LOCKED_SCRIPTS**: Boolean, whether to show locked scripts as disabled or hide them entirely. (Defalt: True -- show as disabled)

# <a name="s3"></a>Remote File Systems

Djangui has been tested on heroku with S3 as a file storage system. Settings for this can be seen in the user_settings.py, which give you a starting point for a non-local server. In short, you need to change your storage settings like such:

<code>

STATICFILES_STORAGE = DEFAULT_FILE_STORAGE = 'djangui.djanguistorage.CachedS3BotoStorage'
DJANGUI_EPHEMERAL_FILES = True

</code>
