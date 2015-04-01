# -*- coding: utf-8 -*-
'''Public section, including homepage and signup.'''
from flask import (Blueprint, request, render_template, flash, url_for,
                   redirect, session, abort, send_from_directory, jsonify)
from flask.ext.login import login_user, login_required, logout_user, current_user

from wooey.extensions import login_manager
from wooey.user.models import User
from wooey.public.forms import LoginForm
from wooey.user.forms import RegisterForm
from wooey.utils import flash_errors
from wooey.database import db

from werkzeug import secure_filename

from collections import defaultdict

import tempfile

import json
import os
import base64
import mistune

import zipfile, tarfile

from .models import Script, Job, STATUS_COMPLETE

blueprint = Blueprint('public', __name__, static_folder="../static")


@login_manager.user_loader
def load_user(id):
    return User.get_by_id(int(id))


@blueprint.route("/", methods=["GET", "POST"])
def home():
    form = LoginForm(request.form)
    # Handle logging in
    if request.method == 'POST':
        if form.validate_on_submit():
            login_user(form.user)
            flash("You are logged in.", 'success')
            redirect_url = request.args.get("next") or url_for("user.members")
            return redirect(redirect_url)
        else:
            flash_errors(form)

    scripts = Script.query.order_by(Script.name)
    return render_template("public/home.html", form=form, scripts=scripts)


@blueprint.route('/logout/')
@login_required
def logout():
    logout_user()
    flash('You are logged out.', 'info')
    return redirect(url_for('public.home'))


@blueprint.route("/register/", methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        new_user = User.create(username=form.username.data,
                               email=form.email.data,
                               password=form.password.data,
                               active=True)
        flash("Thank you for registering. You can now log in.", 'success')
        return redirect(url_for('public.home'))
    else:
        flash_errors(form)
    return render_template('public/register.html', form=form)


@blueprint.route("/about/")
def about():
    form = LoginForm(request.form)
    return render_template("public/about.html", form=form)


@blueprint.route("/scripts/")
def scripts():
    scripts = Script.query.order_by(Script.name)
    return render_template("public/scripts.html", scripts=scripts)


@blueprint.route("/jobs/create/<int:script_id>/", methods=["GET", "POST"])
def create_job(script_id):
    '''
    Create a new job from the given script.

    GET request results in rendering the form
    POST accepts the form, creates the job and redirects to the job view

    This function handles the conversion of POSTed data into a command line arg sequence for
    subsequent running as a job object.

    :param script_id:
    :return:
    '''

    # Get the script object from the database
    script = Script.query.get(script_id)

    if request.method == 'GET':
        # Find the documentation and parse it using markdown
        documentation = script.load_docs()
        if documentation:
            documentation = mistune.markdown(documentation)

        # Render the script view
        return render_template("public/job.html", script=script, metadata=script.load_config(),
                               documentation=documentation)

    elif request.method == 'POST':
        # Handle the form submission to generate the arguments for the script
        metadata = script.load_config()

        args = []
        tempdir = tempfile.mkdtemp()

        for l in ['required', 'optional']:
            for a in metadata[l]:
                # Positional arguments
                name = a['name']

                if (name in request.form and request.form[name]) or \
                        (name in request.files and request.files[name]):

                    # Add the command switch if defined
                    if a['commands']:
                        args.append(a['commands'][0])

                    if name in request.form:

                        # Required arguments are positional; so plot it into place
                        # FIXME: Probably a better check to do here, might require additional data from the parser
                        if a['widget'] not in ["CheckBox"]:
                            if a['nargs'] == '+' or a['nargs'] == '*':
                                args.extend(request.form[name].split(" "))
                            else:
                                args.append(request.form[name])

                    elif name in request.files:
                        # FIXME: Should account for the EXCLUDED UPLOAD in settings.py
                        # Process file upload. We need to copy to a temporary file and update the dictionary
                        file = request.files[name]
                        fname = os.path.join(tempdir, secure_filename(file.filename))
                        file.save(fname)
                        args.append(fname)

        # Create the job
        # FIXME: Priority should be calculated from the higest value of the script and the user
        # e.g. a user with priority 10 running a priority 1 script, will get a priority 10 job

        if current_user.is_anonymous():
            # Allow non-logged in users to submit public jobs
            user = None
        else:
            user = current_user

        job = Job(script=script, user=user, path=tempdir, config=json.dumps({'args': args}), priority=script.priority)
        db.session.commit()

        return redirect(url_for('public.job', job_id=job.id))


def build_display_objects(files):

    display = defaultdict(list)

    for filename in sorted(files):

        name, ext = os.path.splitext(os.path.basename(filename))

        if ext in ['.png', '.jpg', '.jpeg', '.tif', '.tiff']:
            with open(filename, 'r') as f:
                src = '<img src="data:image/' + ext + ';base64,' + base64.b64encode(f.read()) + '">'
                size = f.tell()

            display['Images'].append({
                'name': name,
                'src': src,
                'icon': 'file-image-o',
                'metadata': ["%dkB" % (size / 1024), 'image/%s' % ext[1:]]
            })

        elif ext in ['.svg']:
            with open(filename, 'r') as f:
                src = f.read().decode('utf8')
                size = f.tell()

            display['Images'].append({
                'name': name,
                'src': src,
                'icon': 'file-image-o',
                'metadata': ["%dkB" % (size / 1024), 'image/%s' % ext[1:]]
            })

        elif ext in ['.htm', '.html']:
            with open(filename, 'r') as f:
                src = f.read().decode('utf8')
                size = f.tell()

            display['Html'].append({
                'name': name,
                'src': '<iframe seamless srcdoc="%s" ></iframe>' % src,
                'icon': 'file-text-o',
                'metadata': ["%dkB" % (size / 1024), 'text/%s' % ext[1:]]
            })


        else:  # Miscellaneous files
            size = os.path.getsize(filename)
            display['Other'].append({
                'name': name,
                'src': "",
                'icon': 'file-o',
                'metadata': ["%dkB" % (size / 1024), ext[1:].upper()]
            })

    return display


@blueprint.route("/jobs/<int:job_id>/")
def job(job_id):
    '''
    View a single job (any status) with AJAX callback to update elements, e.g.
        - STDOUT/STDERR
        - File outputs (figures, etc.), intelligent render handling
        - Download link for all files


    :param job_id:
    :return:
    '''

    # Get the job object from the database
    job = Job.query.get(job_id)
    script = job.script
    display = {}

    cwd = os.path.join(job.path, 'output')  # Excution path of the job
    if os.path.isdir(cwd):  # Execution has begun/finished

        files = job.get_output_files()
        display = build_display_objects(files)

    documentation = script.load_docs()
    if documentation:
        documentation = mistune.markdown(documentation)

    return render_template("public/job.html", script=script, job=job, metadata=script.load_config(), display=display,
                           documentation=documentation)


@blueprint.route("/jobs/<int:job_id>.json")
def job_json(job_id):
    '''
    Get the current job status information by AJAX, sufficient to update the current view with output.

    This will be polled every 5s on running jobs.

    :param job_id:
    :return:
    '''

    job = Job.query.get(job_id)

    files = job.get_output_files()
    if files:
        displayo = build_display_objects(files)

    display = {}
    for section, oo in displayo.items():
        display[section] = {
            'count': len(oo),
            'content': render_template("public/job_content.html", section=section, oo=sorted(oo)),
            }

    data = {
        'status': job.status,
        'updated_at': job.updated_at,
        'started_at': job.started_at,
        'stopped_at': job.stopped_at,
        'priority': job.priority,
        'console': job.console,  # Might be a bit heavy on disk access
        'has_output': job.has_output, # Might be a bit heavy on disk access
        'display': display,
    }

    return jsonify(**data)


def make_zipdir(zipf, path):
    for root, dirs, files in os.walk(path):
        for file in files:
            fn = os.path.join(root, file)
            zipf.write(fn, os.path.relpath(fn, path))


@blueprint.route("/jobs/<int:job_id>/download<format>")
def download_job_output(job_id, format):
    if format not in ['.zip', '.tgz', '.tar.gz']:
        abort(404)

    job = Job.query.get(job_id)

    if job.stopped_at is None:
        # Don't return (or generate) a download until the job is stopped (error or complete)
        abort(404)

    fn = secure_filename("%s_%d%s" % (job.script.name, job.id, format))
    path_fn = os.path.join(job.path, fn)

    # Check for existence of pre-zipped files
    if not os.path.exists(path_fn):

        # Target folder to zip
        folder = os.path.join(job.path, 'output')

        if format == '.zip':
            with zipfile.ZipFile(path_fn, 'w', zipfile.ZIP_DEFLATED) as zipf:
                make_zipdir(zipf, folder)

        elif format in ['.tar.gz', '.tgz']:

            with tarfile.open(path_fn, "w:gz") as tarzf:
                tarzf.add(folder, arcname="")

    # Return the download
    return send_from_directory(job.path, fn, as_attachment=True)


@blueprint.route("/queue/")
def queue():
    jobs = Job.query.order_by(Job.created_at.desc())
    return render_template("public/queue.html", jobs=jobs)
