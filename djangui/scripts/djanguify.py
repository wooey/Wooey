#!/usr/bin/env python
__author__ = 'chris'
description = """
Convert things to django
"""
import sys
import traceback
import os
import imp
import subprocess
from argparse import ArgumentParser
from django.template import Context, Engine
from django.utils.crypto import get_random_string

from djangui.backend.nodes import ArgParseNodeBuilder


def main():
    parser = ArgumentParser(description=description)
    parser.add_argument('-s', '--scripts', help='A file or folder to look for scripts.', type=str, required=True)
    parser.add_argument('-r', '--recursive', help='Recursively search for scripts.', action='store_true')
    parser.add_argument('-a', '--app', help='The name of the app to create.', type=str, required=True)
    parser.add_argument('-p', '--project', help='The name of the django project to create.', type=str)
    parser.add_argument('--fake', help='Dont do anything.', action='store_true')
    args = parser.parse_args()
    scripts_path = args.scripts
    scripts = []
    if os.path.isdir(scripts_path):
        if args.recursive:
            for root, folders, files in os.path.walk(scripts_path):
                scripts += [os.path.join(root, filename) for filename in files if filename.endswith('.py')]
        else:
            scripts += [os.path.join(scripts_path, filename) for filename in os.listdir(scripts_path) if filename.endswith('.py')]
    else:
        scripts.append(scripts_path)

    project_name = args.project
    app_name = args.app
    app_base_dir = ''
    if project_name:
        if not args.fake:
            subprocess.call(['django-admin.py', 'startproject', project_name])
        project_base_dir = os.path.join(app_base_dir, project_name, project_name)
        app_base_dir = os.path.join(app_base_dir, project_name)
    app_base_dir = os.path.join(app_base_dir, app_name)

    if not args.fake:
        com = ['django-admin.py', 'startapp', app_name]
        if project_name:
            app_path = os.path.join(os.path.abspath(project_name), app_name)
            os.mkdir(app_path)
            com.append(app_path)
        print com
        subprocess.call(com)

    djanguify_folder = os.path.split(os.path.realpath(__file__))[0]
    app_template_dir = os.path.join(djanguify_folder, '..', 'conf', 'script_template')
    project_template_dir = os.path.join(djanguify_folder, '..', 'conf', 'project_template')

    app_models = []

    for script in scripts:
        arg_nodes = {}
        basename, extension = os.path.splitext(script)
        basename = basename.lower()
        filename = os.path.split(basename)[1]
        try:
            module = imp.load_source(basename, script)
        except:
            sys.stderr.write('Error while loading %s:\n'.format(script))
            sys.stderr.write('{0}\n'.format(traceback.format_exc()))
            continue
        module_parser = module.parser
        parser = ArgParseNodeBuilder(filename, module_parser)
        app_models.append(parser.getModelDict())

    secret_chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    context = Context(
        dict({
            'app_name': app_name,
            'project_name': project_name,
            'secret_key': get_random_string(50, secret_chars),
        },
        **{
            'models': app_models,
        }),
        autoescape=False
    )

    template_files = []
    def walk_dir(templates, dest):
        l = []
        for root, folders, files in os.walk(templates):
            for filename in files:
                relative_dir = '.{0}'.format(os.path.split(os.path.join(root, filename).replace(templates, ''))[0])
                l.append((os.path.join(root, filename), os.path.join(dest, relative_dir)))
        return l

    template_files += walk_dir(app_template_dir, app_base_dir)
    template_files += walk_dir(project_template_dir, project_base_dir)

    for template_file, dest_dir in template_files:
        template_file = open(template_file)
        content = template_file.read()
        content = content.decode('utf-8')
        template = Engine().from_string(content)
        content = template.render(context)
        content = content.encode('utf-8')
        # import pdb; pdb.set_trace();
        to_name = os.path.join(dest_dir, os.path.split(template_file.name)[1])
        # print template_file, dest_dir, to_name
        try:
            os.mkdir(dest_dir)
        except:
            pass
        with open(to_name, 'wb') as new_file:
            new_file.write(content)

if __name__ == "__main__":
    sys.exit(main())