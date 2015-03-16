import os
import json
import logging

from . import argparse_to_json
from . import source_parser
from argparse import ArgumentParser


def collect_argparses(files, write_out_json=True):

    build_specs = []

    for filepath in files:
        _, filename = os.path.split(filepath)

        with open(filepath, 'r') as f:
            source = f.read()

        if not has_argparse(source):
            continue  # Skip files without argparses

        logging.info("Processing file %s." % filepath)

        run_cmd = 'python {}'.format(filepath)

        try:
            ast_source = source_parser.parse_source_file(filepath)
            python_code = source_parser.convert_to_python(list(ast_source))
        except Exception as e:  # Catch all exceptions and report, but continue
            logging.error("Compilation of script %s failed with: %s" % (filepath, e))
            continue  # Next script

        globals = {}
        # Now execute the code to get the argparse object
        try:
            exec('\n'.join(python_code), globals)

        except Exception as e:  # Catch all exceptions and report, but continue
            logging.error("Execution of script %s failed with: %s" % (filepath, e))
            continue  # Next script

        parsers = [p for k, p in globals.items() if isinstance(p, ArgumentParser)]

        if parsers:
            parser = parsers[0]  # Why would there be more than 1?
            build_spec = argparse_to_json.convert(parser)

            build_spec['program'] = {
                'name': os.path.splitext(os.path.basename(filepath))[0],
                'path': os.path.realpath(filepath),
                'description': parser.description,
                'epilog': parser.epilog,
            }

            build_spec['parser'] = {
                'prefix_chars': parser.prefix_chars,
                'argument_default': parser.argument_default,
            }

            # Write out spec alongside the file?
            outfile = os.path.splitext(filepath)[0] + '.json'
            with open(outfile, 'w') as f:
                json.dump(build_spec, f, indent=4)

            # Store to return
            build_specs.append(build_spec)

    return build_specs


def has_argparse(source):
    bla = ['.parse_args()' in line.lower() for line in source.split('\n')]
    return any(bla)
