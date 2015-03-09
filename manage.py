#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import json
import time

from flask.ext.script import Manager, Shell, Server
from flask.ext.migrate import MigrateCommand

from wooey.app import create_app
from wooey.user.models import User
from wooey.settings import DevConfig, ProdConfig
from wooey.database import db

from wooey.backend.utils import find_files
from wooey.backend.python import collect_argparses

from wooey.public.models import Script, Job, STATUS_WAITING, STATUS_COMPLETE, STATUS_ERROR, STATUS_RUNNING

import select

if os.environ.get("WOOEY_ENV") == 'prod':
    app = create_app(ProdConfig)
else:
    app = create_app(DevConfig)

HERE = os.path.abspath(os.path.dirname(__file__))
TEST_PATH = os.path.join(HERE, 'tests')

manager = Manager(app)


def _make_context():
    """Return context dict for a shell session so you can access
    app, db, and the User model by default.
    """
    return {'app': app, 'db': db, 'User': User}


@manager.command
def test():
    """Run the tests."""
    import pytest
    exit_code = pytest.main([TEST_PATH, '--verbose'])
    return exit_code

manager.add_command('server', Server())
manager.add_command('shell', Shell(make_context=_make_context))
manager.add_command('db', MigrateCommand)


@manager.command
def build_scripts():
    '''
    Build script JSON data for UIs (default), don't overwrite

    :return:
    '''

    scripts = find_files(os.path.join('.', 'scripts'), '.py')
    collect_argparses(scripts)


@manager.command
def find_scripts():
    '''
    Loader that iterates over script config folder, reading JSON files and updating the
    admin config to store. The config itself is not loaded (parsed and managed on output).

    :return:
    '''

    jsons = find_files(os.path.join('.', 'scripts'), '.json')

    for json_filename in jsons:
        # Extract to dict structure, then interrogate the database to see if we already have this and update
        with open(json_filename, 'r') as f:
            jo = json.load(f)

        full_path = os.path.realpath(json_filename)

        # Try query the db for object with the same (?hash)
        script = Script.query.filter_by(config_path=full_path).first()  # Will be only one
        if not script:
            script = Script(config_path=full_path)  # Create it

        # Amend the object
        script.exec_path = jo['program']['path']
        script.description = jo['program']['description']
        script.name = jo['program']['name']

        if 'documentation' in jo['program']:
            script.doc_path = jo['program']['documentation']
        elif os.path.exists(os.path.splitext(script.exec_path)[0] + '.md'):
            script.doc_path = os.path.splitext(script.exec_path)[0] + '.md'
        elif os.path.exists(os.path.splitext(script.config_path)[0] + '.md'):
            script.doc_path = os.path.splitext(script.config_path)[0] + '.md'

        db.session.add(script)
        db.session.commit()


def read_all_so_far(proc, out=''):
    while (select.select([proc.stdout], [], [], 0)[0] != []):
        out += proc.stdout.read(1)
    return out


@manager.command
def start_daemon():
    '''
    Infinitely loop, checking the database for waiting Jobs and executing them.

    This is nasty.

    Keep handles to subprocesses so we can kill them if receiving signal (via database) from user/admin.


    :return:
    '''

    # Track the Popen objects for each, dict to map via Job PK
    pids = {}

    # Initialise by setting all running jobs to error (must have died on previous execution)
    Job.query.filter(Job.status == STATUS_RUNNING).update({Job.status: STATUS_ERROR})
    db.session.commit()



    while True:
        # Query the database for running jobs

        jobs_running = Job.query.filter(Job.status == STATUS_RUNNING)
        no_of_running_jobs = jobs_running.count()

        for job in jobs_running:
            print(job)


        # Check each vs. running subprocesses to see if still active (if not, update database with new status)
        for k, v in pids.items():

            # Check process status and flush to file
            v['pid'].poll()

            if v['pid'].returncode is None:  # Still running
                pass
            else:
                try:
                    v['out'].close()
                except IOError:
                    pass

                if v['pid'].returncode == 0:  # Complete
                    job = Job.query.get(k)
                    job.status = STATUS_COMPLETE

                else:  # Error
                    job = Job.query.get(k)
                    job.status = STATUS_ERROR

                # Delete the process object
                del pids[k]
                db.session.commit()


        # If number of running jobs < MAX_RUNNING_JOBS start some more
        if no_of_running_jobs < 5:
            jobs_to_run = Job.query.filter(Job.status == STATUS_WAITING).order_by(Job.created_at.desc())
            for job in jobs_to_run:

                # Get the config settings from the database (dict of values via JSON)
                if job.config:
                    config = json.loads(job.config)
                else:
                    config = {}

                # Get args from the config dict (stored in job)
                args = config['args']

                # Add the executable to the beginning of the sequence
                args.insert(0, job.script.exec_path)

                print(' '.join(args))

                out = open(os.path.join(job.path, 'STDOUT'), 'w')
                # Run the command and store the object for future use
                pids[job.id] = {
                    'pid': subprocess.Popen(args, cwd=job.path, stdout=out, stderr=subprocess.STDOUT),
                    'out': out,
                    }

                # Update the job status
                job.status = STATUS_RUNNING
                db.session.commit()

        print(pids)
        time.sleep(5)






if __name__ == '__main__':
    manager.run()
