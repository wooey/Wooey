import sys
import os
import subprocess
import shutil
from argparse import ArgumentParser
from django.template import Context

# This is needed on django 1.9
from .. version import DJANGO_VERSION, DJ19, DJ110
if DJANGO_VERSION >= DJ19:
    from django.conf import settings
    import django
    extra_settings = {}
    if DJANGO_VERSION >= DJ110:
        extra_settings['TEMPLATES'] = [{'BACKEND': 'django.template.backends.django.DjangoTemplates',}]
    settings.configure(**extra_settings)
    django.setup()

import wooey

from .. import django_compat


def which(pgm):
    # from http://stackoverflow.com/questions/9877462/is-there-a-python-equivalent-to-the-which-command
    path=os.getenv('PATH')
    for p in path.split(os.path.pathsep):
        p=os.path.join(p, pgm)
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p


def walk_dir(templates, dest, filter=None):
    l = []
    for root, folders, files in os.walk(templates):
        for filename in files:
            if filename.endswith('.pyc') or (filter and filename not in filter):
                continue
            relative_dir = '.{0}'.format(os.path.split(os.path.join(root, filename).replace(templates, ''))[0])
            l.append((os.path.join(root, filename), os.path.join(dest, relative_dir)))
    return l


def bootstrap(env=None, cwd=None):
    if env is None:
        env = os.environ
    parser = ArgumentParser(description="Create a Django project with a Wooey app included.")
    parser.add_argument('-p', '--project', help='The name of the django project to create.', type=str, required=True)
    args = parser.parse_args()

    project_name = args.project
    new_project = not os.path.exists(project_name)
    if not new_project:
        sys.stderr.write('Project {0} already exists.\n'.format(project_name))
        sys.exit(1)
    env['DJANGO_SETTINGS_MODULE'] = ''
    admin_command = [sys.executable] if sys.executable else []
    admin_path = which('django-admin.py')
    if admin_path is None:
        # on windows, we may need to look for django-admin.exe
        platform = sys.platform
        if platform == "win32":
            admin_path = which('django-admin')
            if admin_path is None:
                admin_path = which('django-admin.exe')
                if admin_path is not None:
                    admin_command = []
    if admin_path is None:
        sys.stderr.write('Unable to find django-admin command. Please check your PATH and ensure django-admin is accessible.\n')
        sys.exit(1)
    admin_command.extend([admin_path, 'startproject', project_name])
    admin_kwargs = {'env': env}
    if cwd is not None:
        admin_kwargs.update({'cwd': cwd})
    subprocess.call(admin_command, **admin_kwargs)
    project_root = project_name
    project_base_dir = os.path.join(os.path.realpath(os.path.curdir), project_root, project_name)

    wooify_folder = os.path.split(os.path.realpath(wooey.__file__))[0]
    project_template_dir = os.path.join(wooify_folder, 'conf', 'project_template')

    context = Context(
        dict({
            'project_name': project_name,
        },
        autoescape=False
    ))

    template_files = []

    template_files += walk_dir(project_template_dir, project_base_dir)

    for template_file, dest_dir in template_files:
        template_file = open(template_file)
        content = template_file.read()
        template = django_compat.get_template_from_string(content)
        content = template.render(context)
        content = content.encode('utf-8')
        to_name = os.path.join(dest_dir, os.path.split(template_file.name)[1])
        try:
            os.mkdir(dest_dir)
        except:
            pass
        with open(to_name, 'wb') as new_file:
            new_file.write(content)

    # move the django settings to the settings path so we don't have to chase Django changes.
    shutil.move(os.path.join(project_base_dir, 'settings.py'), os.path.join(project_base_dir, 'settings', 'django_settings.py'))
    # do the same with urls
    shutil.move(os.path.join(project_base_dir, 'urls.py'), os.path.join(project_base_dir, 'urls', 'django_urls.py'))
    env['DJANGO_SETTINGS_MODULE'] = '.'.join([project_name, 'settings', 'user_settings'])
    subprocess.call(['python', 'manage.py', 'migrate'], env=env, cwd=project_root)
    subprocess.call(['python', 'manage.py', 'createcachetable'], env=env, cwd=project_root)
    subprocess.call(['python', 'manage.py', 'collectstatic', '--noinput'], env=env, cwd=project_root)
    sys.stdout.write("Please enter the project directory {0}, and run python manage.py createsuperuser and"
                     " python manage.py runserver to start. The admin can be found at localhost:8000/admin. You may also want to set your "
                     "DJANGO_SETTINGS_MODULE environment variable to {0}.settings \n".format(project_name))
