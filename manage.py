#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import errno
import subprocess
import json
import time
import datetime as dt
import shutil
import datetime as dt

from flask.ext.script import Manager, Shell, Server
from flask.ext.migrate import MigrateCommand
from flask.ext.assets import ManageAssets

from sqlalchemy import or_

from wooey.app import create_app
from wooey.user.models import User
from wooey.settings import DevConfig, ProdConfig
from wooey.database import db

from wooey.backend.utils import find_files
from wooey.backend.python import collect_argparses

from wooey.public.models import Script, Job, STATUS_WAITING, STATUS_COMPLETE, STATUS_ERROR, STATUS_RUNNING


import select

import logging
logging.basicConfig(level=logging.DEBUG)




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

    for f in app.config.get('SCRIPT_FOLDERS'):
        scripts = find_files(f, '.py')
        collect_argparses(scripts)


@manager.command
def find_scripts():
    '''
    Loader that iterates over script config folder, reading JSON files and updating the
    admin config to store. The config itself is not loaded (parsed and managed on output).

    :return:
    '''

    for f in app.config.get('SCRIPT_FOLDERS'):

        jsons = find_files(f, '.json')

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


def mkdirs(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise



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

    try:
        while True:
            # Query the database for running jobs

            jobs_running = Job.query.filter(Job.status == STATUS_RUNNING)
            no_of_running_jobs = jobs_running.count()

            # Check each vs. running subprocesses to see if still active (if not, update database with new status)
            for k, v in pids.items():

                # Check process status and flush to file
                v['process'].poll()

                if v['process'].returncode is None:  # Still running
                    pass
                else:
                    try:
                        v['out'].close()
                    except IOError:
                        pass

                    if v['process'].returncode == 0:  # Complete
                        logging.info("Job %d completed successfully." % job.id)
                        job = Job.query.get(k)
                        job.status = STATUS_COMPLETE

                    else:  # Error
                        logging.error("Job %d exited with an error status." % job.id)
                        job = Job.query.get(k)
                        job.status = STATUS_ERROR

                    # Delete the process object
                    del pids[k]
                    job.stopped_at = dt.datetime.utcnow()
                    db.session.commit()


            # If number of running jobs < MAX_RUNNING_JOBS start some more
            if no_of_running_jobs < app.config.get('QUEUE_MAXIMUM_RUNNING_JOBS'):

                # Get the waiting jobs (STATUS_WAITING) ordered by the age-in-minutes/priority DESC
                # Jobs with a priority of `1` will sort above equally-old jobs with a higher priority value
                # A job that is priority `2` will sort equal with a job half it's age
                jobs_to_run = Job.query.filter(Job.status == STATUS_WAITING).order_by(Job.created_at)


                for job in jobs_to_run[:app.config.get('QUEUE_MAXIMUM_RUNNING_JOBS')]:

                    # We wrap the entire execution block in a try-except to catch all errors that may be thrown
                    # without dying. Errors at a lower level are raised to this catch-all.
                    try:

                        # Get the config settings from the database (dict of values via JSON)
                        if job.config:
                            try:
                                config = json.loads(job.config)
                                # Get args from the config dict (stored in job)
                                args = config['args']
                            except Exception:
                                raise

                        else:
                            args = []


                        # Add the executable to the beginning of the sequence
                        args.insert(0, job.script.exec_path)

                        try:
                            out = open(os.path.join(job.path, 'STDOUT'), 'w')

                        except Exception:
                            raise

                        cwd = os.path.join(job.path, 'output')
                        try:
                            # Create folder, accepting it already exists (re-run of previous job is OK)
                            mkdirs(cwd)

                        except Exception:
                            raise

                        logging.info("Starting job %d." % job.id)

                        # On Windows we need to supply the python executable as a first argument
                        if sys.platform == 'win32':

                            if sys.version_info >= (3, 3):
                                # On python 3.3+ use py launcher
                                args.insert(0, 'py')

                            else:
                                # On python <3.3 use python executable
                                args.insert(0, 'python')

                        try:
                            # Run the command and store the object for future use
                            process = subprocess.Popen(args, cwd=cwd, bufsize=0, stdout=out, stderr=subprocess.STDOUT)

                        except Exception:
                            raise

                        pids[job.id] = {
                            'process': process,
                            'out': out,
                        }

                        # Update the job status
                        job.status = STATUS_RUNNING
                        job.started_at = dt.datetime.utcnow()
                        job.pid = process.pid

                        db.session.commit()

                    except Exception as e:
                        # Anything goes wrong here we stop; log the error; set the status and try the next
                        logging.error(e.message)
                        job.status = STATUS_ERROR
                        db.session.commit()
                        continue  # Next job

            time.sleep(1)

    except KeyboardInterrupt:
        pass

    # Shutdown nicely
    logging.info("Shutting down...")
    # Set all running jobs to error (will die when we close)
    Job.query.filter(Job.status == STATUS_RUNNING).update({Job.status: STATUS_ERROR})
    db.session.commit()

    # Check each vs. running subprocesses to see if still active (if not, update database with new status)
    for k, v in pids.items():
        v['process'].kill()  # Kill the running process
        v['out'].close()  # Close the output file
        del pids[k]  # Delete the object

    logging.info("Done.")


@manager.command
def cleanup():

    # Initialise by setting all running jobs to error (must have died on previous execution)
    old_jobs = Job.query.filter( or_(Job.status == STATUS_ERROR, Job.status == STATUS_COMPLETE) ).order_by(Job.created_at)[:-app.config.get('QUEUE_MAXIMUM_FINISHED_JOBS')]

    for job in old_jobs:
        # Delete the files for this job (recover space)
        shutil.rmtree( job.path )
        job.delete()
    db.session.commit()

# Asset management
manager.add_command("assets", ManageAssets())


if __name__ == '__main__':
    manager.run()
