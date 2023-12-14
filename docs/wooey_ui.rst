Wooey UI
=============

Wooey's homepage provides a list of all scripts available to a user.

.. image:: img/Wooey_Home.png

From here, a user can choose a script to configure for execution. On all pages
a header menu is available that provides the number of running scripts, the
number of queued scripts, and the number of scripts that has finished executing.
Users can select these header items for further inspection of pending or completed
jobs. Additionally, there is a *scrapbook* where a user can save results from previous
jobs for easy access and a language menu item for translation of Wooey's interface
to various languages (If your language is not currently supported, we would love to
add it!).

Running scripts
---------------

Scripts may be accessed via the homepage or by searching for scripts in the
script search. Searching for scripts is accessible via the left menu sidebar
that is viewable by clicking the menu button on the left side of the header.
From the script panel, scripts can be parameterized and executed by Wooey.
If a script has subparsers, they are accessible via a dropdown menu on
the upper left of the script parameter panel (in a script with subparsers,
this simply has the text *Settings*). Because most subparsers have a "main"
parser, such as Django's `manage.py`, these settings can be specified via
the *Main Parser Parameter* button. To select and parameterize a given
subparser, the subparser command and its parameters are available by
selecting it via the dropdown menu.

Running previous versions of a script
-------------------------------------

Previously uploaded scripts are kept in Wooey, providing a mechanism for
to evaluate script changes and give end-users an opportunity to provide
feedback. In the admin interface, there is an option to set a script version
as the *default* version to use, but previous versions are accessible from
the main UI via the black down array next to the script name. There are 2
deliniations specified here -- the *Script Version*, and the *Script Iteration*.
If a command line generating tool supports versioning (and Wooey is able
to parse this information), updates to the script version will result in a new
version being created. If a command line library doesn't support versioning
or the version has not been updated in a script, the Script Iteration counter
will be incremented.

Using URL parameters to pre-populate script parameters
------------------------------------------------------

Wooey supports pre-populating script parameters via URL parameters. This is
useful for providing a link to a script with some parameters already set. The
following rules apply.

* URL parameters are specified as :code:`?parameter=value`
* Multiple parameters may be specified by separating them with :code:`&`.
  For example, :code:`?parameter1=value1&parameter2=value2`.
* Parameters are specified by the name used in the script, **but in snake case**.
  For example, a parameter named :code:`--my-parameter` would be specified as
  :code:`?my_parameter=value`.
* If a parameter is a flag, passing any value will set the flag. For example,
  :code:`?my_flag=1` or :code:`?my_flag=true` will set the flag.
* If a parameter accepts multiple values (:code:`nargs`), the values are specified
  by passing the parameter multiple times. For example, :code:`?my_parameter=1&my_parameter=2`
  will set the parameter to have two values filled out: :code:`1` and :code:`2`.
  If a parameter does not support multiple values and multiple values are passed,
  the last value will be used.
* If the script has subparsers, the :code:`__subparser` parameter is used to specify
  the subparser to use. For example, :code:`?__subparser=mysubparser` will select the
  subparser named :code:`mysubparser`.
