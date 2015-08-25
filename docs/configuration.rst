Configuration
=============

**WOOEY\_FILE\_DIR**: String, where the files uploaded by the user will
be saved (Default: wooey\_files)

**WOOEY\_CELERY**: Boolean, whether or not celery is enabled. If
disabled, tasks will run locally and block execution. (Default: True)

**WOOEY\_CELERY\_TASKS**: String, the name of the celery tasks for
Wooey. (Default: 'wooey.tasks')

**WOOEY\_ALLOW\_ANONYMOUS**: Boolean, whether to allow submission of
jobs by anonymous users. (Default: True)

By default, Wooey has a basic user account system. It is very basic, and
doesn't confirm registrations via email.

**WOOEY\_AUTH**: Boolean, whether to use the authorization system of
Wooey for simple login/registration. (Default: True)

**WOOEY\_LOGIN\_URL**: String, if you have an existing authorization
system, the login url: (Default: settings.LOGIN\_URL

**WOOEY\_REGISTER\_URL**: String, if you have an existing authorization
system, the registration url: (Default: /accounts/register/)

**WOOEY\_EPHEMERAL\_FILES**: Boolean, if your file system changes with
each restart. (Default: False)

**WOOEY\_SHOW\_LOCKED\_SCRIPTS**: Boolean, whether to show locked
scripts as disabled or hide them entirely. (Defalt: True -- show as
disabled)
