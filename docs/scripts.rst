Adding & Managing Scripts
=========================

Scripts may be added in two ways, through the Django admin interface as
well as through the *addscript* command in manage.py.

Script Guidelines
-----------------

The easiest way to make your scripts compatible with Wooey is to define
your ArgParse class in the global scope. For instance:

::


    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Find the sum of all the numbers below a certain number.")
    parser.add_argument('--below', help='The number to find the sum of numbers below.', type=int, default=1000)

    def main():
        args = parser.parse_args()
        s = sum((i for i in range(args.below)))
        print("Sum =", s)
        return 0

    if __name__ == "__main__":
        sys.exit(main())


If you have failing scripts, please open an issue with their contents so
we can handle cases as they appear and try to make this as
all-encompasing as possible. One known area which fails currently is
defining your argparse instance inside the
``if __name__ == "__main__"`` block


The admin Interface
-------------------

Within the django admin interface, scripts may be added to through the
'scripts' model. Here, the user permissions may be set, as well as
cosmetic features such as the script's display name, description (if
provided, otherwise the script name and description will be
automatically populated by the description from argparse if available).

The command line
----------------

``./manage.py addscript``

This will add a script or a folder of scripts to Wooey (if a folder is
passed instead of a file). By default, scripts will be created in the
'Wooey Scripts' group.

Script Organization
-------------------

Scripts can be viewed at the root url of Wooey. The ordering of scripts,
and groupings of scripts can be altered by changing the 'Script order'
or 'Group order' options within the admin.

Script Permissions
------------------

Scripts and script groups can be relegated to certain groups of users.
The 'user groups' option, if set, will restrict script usage to users
within selected groups.

Scripts and groups may also be shutoff to all users by unchecked the
'script/group active' option.

Deleting Scripts
----------------

Scripts may be deleted from the admin interface. When deleting a script,
all related objects, such as previously run jobs, will also be deleted.

Other Script Runners
--------------------

There have been several requests for more advanced script setups, such as executing R code or docker.
For now, there is no official integrations with these languages, but it is possible to create a simple
wrapper script that calls docker or another programming language.

.. toctree::
   :maxdepth: 1

   docker_scripts
