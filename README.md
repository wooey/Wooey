# Djangui

Djangui is designed to take scripts implemented with a python command line argument parser (such as argparse), and convert them into a web interface.
 
This project was inspired by how simply and powerfully [sandman](https://github.com/jeffknupp/sandman) could expose users to a database. 
It was also based on my own needs as a data scientist to have a system that could:
    
    1. Autodocument my workflows for data analysis (simple model saving).
    2. Enable fellow lab members with no command line experience to utilize python scripts.
    3. Enable the easy wrapping of any program in simple python instead of having
       to use markup language specific to existing tools such as Galaxy.
       
1. [Installation](#install)
    1. [A Djangui Only Project](#djonly)
    2. [Adding Djangui to Existing Projects](#existing)
2. [Configuration](#config)

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
       
# <a name="config"></a>Configuration

**DJANGUI_FILE_DIR**: String, where the files uploaded by the user will be saved (Default: djangui_files)

**DJANGUI_CELERY**: Boolean, whether or not celery is enabled. If disabled, tasks will run locally and block execution. (Default: True)

**DJANGUI_CELERY_TASKS**: String, the name of the celery tasks for Djangui. (Default: 'djangui.tasks')

**DJANGUI_ALLOW_ANONYMOUS**: Boolean, whether to allow submission of jobs by anonymous users. (Default: True)

By default, Djangui has a basic user account system. It is very basic, and doesn't confirm registrations via email, nor support
password recovery (the admin must reset the passwords).

**DJANGUI_AUTH**: Boolean, whether to use the authorization system of Djangui for simple login/registration. (Default: True)

**DJANGUI_LOGIN_URL**: String, if you have an existing authorization system, the login url: (Default: settings.LOGIN_URL

**DJANGUI_REGISTER_URL**: String, if you have an existing authorization system, the registration url: (Default: /accounts/register/)