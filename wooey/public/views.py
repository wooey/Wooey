# -*- coding: utf-8 -*-
'''Public section, including homepage and signup.'''
from flask import (Blueprint, request, render_template, flash, url_for,
                    redirect, session, abort, send_from_directory)
from flask.ext.login import login_user, login_required, logout_user, current_user

from wooey.extensions import login_manager
from wooey.user.models import User
from wooey.public.forms import LoginForm
from wooey.user.forms import RegisterForm
from wooey.utils import flash_errors
from wooey.database import db

from werkzeug import secure_filename

import tempfile

import json
import os
import base64
import mistune

import zipfile, tarfile

from .models import Script, Job

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

    scripts = Script.query.all()
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
    scripts = Script.query.all()
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
        return render_template("public/create-job.html", script=script, metadata=script.load_config(), documentation=documentation)

    elif request.method == 'POST':
        # Handle the form submission to generate the arguments for the script
        metadata = script.load_config()

        args = []
        tempdir = tempfile.mkdtemp()

        for l in ['required', 'optional']:
            for a in metadata[l]:
                # Positional arguments
                name = a['data']['display_name']

                if (name in request.form and request.form[name]) or \
                   (name in request.files and request.files[name]):

                    # Add the command switch if defined
                    if a['data']['commands']:
                        args.append(a['data']['commands'][0])

                    if name in request.form:

                        # Required arguments are positional; so plot it into place
                        # FIXME: Probably a better check to do here, might require additional data from the parser
                        # FIXME: Also need to handle FILE objects, etc.
                        if a['widget'] not in ["CheckBox"]:
                            if a['data']['nargs'] == '+' or a['data']['nargs'] == '*':
                                args.extend(request.form[name].split(" "))
                            else:
                                args.append(request.form[name])

                    elif name in request.files:
                        # Process file upload. We need to copy to a temporary file and
                        # replace the value in the dictionary (or keep in the same folder, for easier cleanup?)
                        # Will then need a way to identify uploaded vs. output files
                        file = request.files[name]
                        fname = os.path.join(tempdir, secure_filename(file.filename))
                        file.save(fname)
                        args.append(fname)

        # Create the job
        job = Job(script=script, user=current_user, path=tempdir, config=json.dumps({'args': args}))
        db.session.commit()

        return redirect(url_for('public.job', job_id=job.id))


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

    try:
        with open(os.path.join(job.path, 'STDOUT'), 'rU') as f:
            console = f.read().decode('utf8')

    except IOError:
        console = ""


    display = {}
    has_output = False

    cwd = os.path.join(job.path, 'output')  # Excution path of the job
    if os.path.isdir(cwd):  # Execution has begun/finished

        excluded = []

        # Filter files for files and not excluded above list
        # FIXME: The exclude list should come from config
        # FIXME: Add excluded list of *extensions* for download
        files = [f for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f)) and f not in excluded]

        for filename in files:

            fullpath = os.path.join(cwd, filename)
            name, ext = os.path.splitext(filename)
            src = None

            if ext in ['.png', '.jpg', '.jpeg', '.tif', '.tiff']:
                with open(fullpath, 'r') as f:
                    src = '<img src="data:image/' + ext + ';base64,' + base64.b64encode(f.read()) + '">'

            elif ext in ['.svg']:
                with open(fullpath, 'r') as f:
                    src = f.read().decode('utf8')


            if src:
                display[name] = src

        has_output = len(files) > 0

    return render_template("public/job.html", script=script, job=job, metadata=script.load_config(), console=console, display=display, has_output=has_output)


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

    fn = secure_filename("%s_%d%s" % (job.script.name, job.id, format))
    path_fn = os.path.join(job.path, fn )

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


