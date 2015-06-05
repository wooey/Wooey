#!/usr/bin/env python
__author__ = 'chris'
description = """
Create a Django app with Djangui setup.
"""
import sys
import six
import os
import subprocess
import shutil
from argparse import ArgumentParser
from django.template import Context
import djangui
from djangui import django_compat
env = os.environ

def main():
    parser = ArgumentParser(description=description)
    parser.add_argument('-p', '--project', help='The name of the django project to create.', type=str, required=True)
    args = parser.parse_args()

    project_name = args.project
    new_project = not os.path.exists(project_name)
    if not new_project:
        sys.stderr.write('Project {0} already exists.\n'.format(project_name))
        return 1
    env['DJANGO_SETTINGS_MODULE'] = ''
    subprocess.call(['django-admin.py', 'startproject', project_name], env=env)
    project_root = project_name
    project_base_dir = os.path.join(os.path.realpath(os.path.curdir), project_root, project_name)

    djanguify_folder = os.path.split(os.path.realpath(djangui.__file__))[0]
    project_template_dir = os.path.join(djanguify_folder, 'conf', 'project_template')


    context = Context(
        dict({
            'project_name': project_name,
        },
        autoescape=False
    ))

    template_files = []
    def walk_dir(templates, dest, filter=None):
        l = []
        for root, folders, files in os.walk(templates):
            for filename in files:
                if filename.endswith('.pyc') or (filter and filename not in filter):
                    continue
                relative_dir = '.{0}'.format(os.path.split(os.path.join(root, filename).replace(templates, ''))[0])
                l.append((os.path.join(root, filename), os.path.join(dest, relative_dir)))
        return l

    template_files += walk_dir(project_template_dir, project_base_dir)

    for template_file, dest_dir in template_files:
        template_file = open(template_file)
        content = template_file.read()
        content = six.u(content)
        template = django_compat.Engine().from_string(content)
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
    if django_compat.DJANGO_VERSION >= django_compat.DJ17:
        subprocess.call(['python', os.path.join(project_root, 'manage.py'), 'makemigrations'], env=env)
        subprocess.call(['python', os.path.join(project_root, 'manage.py'), 'migrate'], env=env)
    else:
        subprocess.call(['python', os.path.join(project_root, 'manage.py'), 'syncdb', '--noinput'], env=env)
    subprocess.call(['python', os.path.join(project_root, 'manage.py'), 'collectstatic', '--noinput'], env=env)
    sys.stdout.write("Please enter the project directory {0}, and run python manage.py createsuperuser and"
                     " python manage.py runserver to start. The admin can be found at localhost:8000/admin. You may also want to set your "
                     "DJANGO_SETTINGS_MODULE environment variable to {0}.settings \n".format(project_name))
    return 0

if __name__ == "__main__":
    sys.exit(main())