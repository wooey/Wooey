Wooey
=====

Automated web UIs for Python scripts

## About

Wooey is a simple web interface (built on Flask) to run command line Python scripts. Think of it as an easy way to get
your scripts up on the web for routine data analysis, file processing, or anything else.

Impressed by what [Gooey](https://github.com/chriskiehl/Gooey) can do, turning ArgumentParser-based command-line scripts
into WxWidgets-based GUIs, I thought
I'd see if I could do the same for the web. I'm still not sure if the result is beautiful or horrific.

Wooey (see what I did there?) is built on the same, but slightly modified, back-end conversion of ArgumentParser
instances to JSON definitions. These definitions are used to construct a web-based UI with type-dependent widgets.
Submitted configurations are parsed, using the JSON definition, to command line arguments that are then submitted to a job queue.

Jobs in the queue are automatically run and the results made available in the job view, with smart handling of outputs
such as images (CSV, etc. to be supported via pandas, possibly some kind of plugin system) into a tabbed output viewer.
Support for downloading of zipped output files is to follow.

The use case for myself was as a simple platform to allow running of routine data-processing and analysis scripts
within a research group, but I'm sure there are other possibilities. However, I wouldn't recommend putting this
on the public web just yet (pre-alpha warning). It's somewhat comparable to things like Shiny for R, except multi-user
out of the box. Support for multiple command-line formats is on my todo.

Enjoy and please fork.

Built on Flask, using cookiecutter-flask then modified to use the Foundation framework. This is *My First Flask App!*
so please feel free to critique & give pointers. Thanks.


## Walkthrough

The front page of a wooey install presents a list of installed scripts:

![Welcome](welcome_to_wooey.png)

Each script has it's own UI form based on the config parameters defined in the ArgumentParser:

![bar_config example script](bar_config.png)

Documentation can be specified either manually via the JSON, or my providing a
[Markdown](http://en.wikipedia.org/wiki/Markdown)-format file alongside the script or config file.

![plot_some_numbers script with docs](plot_some_numbers_with_documentation.png)

Logged-in users get a nice listing of their previous jobs:

![User job listing](user_job_list.png)

The output from successful jobs is available via an inline viewer (images only presently, .csv support via Pandas to follow):

![Job with success 1](job_success_1.png)
![Job with success 2](job_success_2.png)

Errors are output to the inline console:

![Job with error console](job_with_error.png)



## Quickstart

First, set your app's secret key as an environment variable. For example, example add the following to ``.bashrc`` or ``.bash_profile``.


    export WOOEY_SECRET='something-really-secret'


Then run the following commands to bootstrap your environment.


    git clone https://github.com/mfitzp/wooey
    cd wooey
    pip install -r requirements/dev.txt

At this state you can either install a DBMS or use SQLite as a developer setup.
Either way, run the following to create your app's database tables and perform the initial migration:

    python manage.py db init
    python manage.py db migrate
    python manage.py db upgrade

To add the example scripts to the database and allow you to test
also run:

    python manage.py build_scripts
    python manage.py find_scripts

This will build (create JSON for Python scripts using argparse) and then add them to the database. You can now start up
the server using:

    python manage.py server

In another shell, start the temporary dev 'daemon' (which is nothing of the sort, yet) using:

    python manage.py start_daemon

This looks for jobs in the queue and executes them in a separate process. It's not clever, and it's ugly, but it
achieves what is needed for a proof of concept. In order to actually run scripts you currently need to be a logged-in
user, so create an account on the website and get started. By default all logged in users can see the admin panel at
present but this will change in future.

## Examples

Once you have run `python manage.py build_scripts` and `python manage.py find_scripts` management commands you'll
get the scripts listed in the web UI. Now you can try them out:

1. Example data is provided in `/data` which you can use with the included `bar.py` script. Select to upload with the
file selector, and enter `Glucose|Fructose` in the 'name of metabolite' field. You'll see 4 plots output from the source data.
2. Using the `plot_some_numbers.py` script enter a list of integers separated by spaces, you'll get two plots based on these numbers.
3. Using the `mock_argparse_example.py` script, enter a list of integers separated by spaces,you'll get the max (or sum, if you select this) output in the console.

## Deployment

In your production environment, make sure the ``WOOEY_ENV`` environment variable is set to ``"prod"``.


## Shell

To open the interactive shell, run:

    python manage.py shell

By default, you will have access to ``app``, ``db``, and the ``User`` model. This can be used to quickly recreate database tables
during development, i.e. delete `dev.db` (SQLite) and then from the shell enter:

    db.create_all()


## Running Tests

To run all tests, run:

    python manage.py test


## Migrations

Whenever a database migration needs to be made. Run the following commmands:

    python manage.py db migrate

This will generate a new migration script. Then run:

    python manage.py db upgrade

To apply the migration.

For a full migration command reference, run ``python manage.py db --help``.

## FAQ

### Isn't this terribly insecure?

That largely depends on what you're scripts do. Wooey will perform some standard form-type checking and validation
before passing to your script. The input is then re-parsed (for Python scripts) via ArgumentParser before being
passed into variables in your script. Scripts are also run without invoking a shell (`exec(shell=False)`) which eliminates
shell-interpretation risks. However, if you script does something incredibly silly like taking text input and using it
as a path, you're probably going to regret it.


