.. _wooey-configuration:

Configuration
=============

Wooey Settings
--------------

:code:`WOOEY_ALLOW_ANONYMOUS`: Boolean, whether to allow submission of
jobs by anonymous users. (Default: ``True``)

By default, Wooey has a basic user account system. It is very basic, and
doesn't confirm registrations via email.

:code:`WOOEY_ENABLE_API_KEYS`: Boolean, whether to enable remote authentication
via API Keys.

:code:`WOOEY_AUTH`: Boolean, whether to use the authorization system of
Wooey for simple login/registration. (Default: ``True``)

:code:`WOOEY_CELERY`: Boolean, whether or not celery is enabled. If
disabled, tasks will run locally and block execution. (Default: ``True``)

:code:`WOOEY_CELERY_TASKS`: String, the name of the celery tasks for
Wooey. (Default: ``'wooey.tasks'``)

:code:`WOOEY_DEFAULT_SCRIPT_GROUP`: String, the group scripts should be added
to if no group is specified. (Default: ``'Scripts'``)

:code:`WOOEY_EPHEMERAL_FILES`: Boolean, if your file system changes with
each restart (e.g. files are stored on S3). (Default: ``False``)

:code:`WOOEY_FILE_DIR`: String, where the files uploaded by the user will
be saved (Default: ``wooey_files``)

:code:`WOOEY_JOB_EXPIRATION`: Dictionary, A dictionary with two keys:
:code:`user` and :code:`anonymous`. The values for each is a timedelta
specifying how much time should be elapsed before a job is automatically
deleted. If a key is not provided or :code:`None`, the job for that user
type wll not be deleted.

:code:`WOOEY_LOGIN_URL`: String, if you have an existing authorization
system, the login url: (Default: ``settings.LOGIN_URL``)

:code:`WOOEY_REALTIME_CACHE`: String, the name of the cache to use for
storing real time updates from running jobs.

:code:`WOOEY_REGISTER_URL`: String, if you have an existing authorization
system, the registration url: (Default: ``'/accounts/register/'``)

:code:`WOOEY_SCRIPT_DIR`: String, the folder to save scripts under. It should
be a short, relative path to the storage root. (Default: ``wooey_scripts``)

:code:`WOOEY_SHOW_LOCKED_SCRIPTS`: Boolean, whether to show locked
scripts as disabled or hide them entirely. (Default: ``True`` -- show as
disabled)

:code:`WOOEY_SITE_NAME`: String, the name of the site to display. (Default: ``Wooey!``)

:code:`WOOEY_SITE_TAG`: String, the tagline for the site. (Default: ``A web UI for Python Scripts``)


Internationlization (i18n)
--------------------------

Wooey supports the use of Django internationalization settings to present
the interface in your own language. Currently we provide limited support
for French, German, Dutch, Japanese, and Simplifed Chinese. We welcome
contributions for translation extensions, fixes and new languages from our users.

To specify the default language for your installation, you can specify this using
the :code:`LANGUAGE_CODE` setting in :code:`django_settings.py`.
For example to set the interface to French, you would use:

.. code:: python

  LANGUAGE_CODE = 'fr'


For German you would use:

.. code:: python

  LANGUAGE_CODE = 'de'


If you want the user interface to automatically change to the preferred language
for your visitors, you must use the Django internationalization middleware.
By default, the bootstrapped version of Wooey will add in the necessary middleware,
but for projects using Wooey as a separate app, these projects will need to add
:code:`django.middleware.locale.LocaleMiddleware` to their :code:`MIDDLEWARE`
block in :code:`django_settings.py`. Note that it must come *after* the Session
middleware, and before the CommonMiddleware e.g.

.. code:: python

    MIDDLEWARE = (
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.locale.LocaleMiddleware', # <- HERE
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'django.middleware.security.SecurityMiddleware',
    )

For more information on the internationlization middleware see
`the Django documentation <https://docs.djangoproject.com/en/1.8/topics/i18n/translation/#how-django-discovers-language-preference>`_.

Note that if a user's browser does not request an available language the language
specified in :code:`LANGUAGE_CODE` will be used.
