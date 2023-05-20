Developer Setup
===============

Dev Environment
---------------

Docker
~~~~~~

The `docker` folder contains the Docker setup. Wooey can be built and run by simply
running

::

    docker-compose up --build

To mount the local installation directory in the docker container, create a local version
of the docker-compose overrides by running

::

    cp docker-compose.override.template.yml docker-compose.override.yml

Several convenience scripts exist for common scenarios:

* manage -- run a django-admin command
* run -- run a command in the wooey container. For example, a bash shell can be started by `run bash`
* run-server -- run the Django server that is locally accessible. This offers some advantages over `docker-compose up` such as allowing debugging via `pdb`
* test -- run all unit tests.

System
~~~~~~

For developers not using Docker, dependenices can be installed via

::

    pip install .[dev]

Style
-----

`Pre-commit <https://pre-commit.com/>`_ is used to standardize the tools used for linting and code formatting.
