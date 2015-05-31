'''
Created on Dec 11, 2013

@author: Chris

Collection of functions for extracting argparse related statements from the 
client code.
'''

import ast
import _ast
from itertools import *

from . import codegen


def parse_source_file(file_name):
    """
    Parses the AST of Python file for lines containing
    references to the argparse module.

    returns the collection of ast objects found.

    Example client code:

      1. parser = ArgumentParser(desc="My help Message")
      2. parser.add_argument('filename', help="Name of the file to load")
      3. parser.add_argument('-f', '--format', help='Format of output \nOptions: ['md', 'html']
      4. args = parser.parse_args()

    Variables:
      * nodes                                     Primary syntax tree object
      *    argparse_assignments       The assignment of the ArgumentParser (line 1 in example code)
      * add_arg_assignments     Calls to add_argument() (lines 2-3 in example code)
      * parser_var_name                    The instance variable of the ArgumentParser (line 1 in example code)
      * ast_source                            The curated collection of all parser related nodes in the client code
    """
    with open(file_name, 'r') as f:
        s = f.read()

    nodes = ast.parse(s)

    module_imports = get_nodes_by_instance_type(nodes, _ast.Import)
    specific_imports = get_nodes_by_instance_type(nodes, _ast.ImportFrom)

    assignment_objs = get_nodes_by_instance_type(nodes, _ast.Assign)
    call_objects = get_nodes_by_instance_type(nodes, _ast.Call)

    argparse_assignments = get_nodes_by_containing_attr(assignment_objs, 'ArgumentParser')
    group_arg_assignments = get_nodes_by_containing_attr(assignment_objs, 'add_argument_group')
    add_arg_assignments = get_nodes_by_containing_attr(call_objects, 'add_argument')
    parse_args_assignment = get_nodes_by_containing_attr(call_objects, 'parse_args')
    # there are cases where we have custom argparsers, such as subclassing ArgumentParser. The above
    # will fail on this. However, we can use the methods known to ArgumentParser to do a duck-type like
    # approach to finding what is the arg parser
    if not argparse_assignments:
        aa_references = set([i.func.value.id for i in chain(add_arg_assignments, parse_args_assignment)])
        argparse_like_objects = [getattr(i.value.func, 'id', None) for p_ref in aa_references for i in get_nodes_by_containing_attr(assignment_objs, p_ref)]
        argparse_like_objects = filter(None, argparse_like_objects)
        argparse_assignments = [get_nodes_by_containing_attr(assignment_objs, i) for i in argparse_like_objects]
        # for now, we just choose one
        try:
            argparse_assignments = argparse_assignments[0]
        except IndexError:
            pass


    # get things that are assigned inside ArgumentParser or its methods
    argparse_assigned_variables = get_node_args_and_keywords(assignment_objs, argparse_assignments, 'ArgumentParser')
    add_arg_assigned_variables = get_node_args_and_keywords(assignment_objs, add_arg_assignments, 'add_argument')
    parse_args_assigned_variables = get_node_args_and_keywords(assignment_objs, parse_args_assignment, 'parse_args')

    ast_argparse_source = chain(
        module_imports,
        specific_imports,
        argparse_assigned_variables,
        add_arg_assigned_variables,
        parse_args_assigned_variables,
        argparse_assignments,
        group_arg_assignments,
        add_arg_assignments,
    )
    return ast_argparse_source


def read_client_module(filename):
    with open(filename, 'r') as f:
        return f.readlines()


def get_node_args_and_keywords(assigned_objs, assignments, selector=None):
    referenced_nodes = set([])
    selector_line = -1
    assignment_nodes = []
    for node in assignments:
        for i in walk_tree(node):
            if i and isinstance(i, (_ast.keyword, _ast.Name)) and 'id' in i.__dict__:
                if i.id == selector:
                    selector_line = i.lineno
                elif i.lineno == selector_line:
                    referenced_nodes.add(i.id)
    for node in assigned_objs:
        for target in node.targets:
            if getattr(target, 'id', None) in referenced_nodes:
                assignment_nodes.append(node)
    return assignment_nodes


def get_nodes_by_instance_type(nodes, object_type):
    return [node for node in walk_tree(nodes) if isinstance(node, object_type)]


def get_nodes_by_containing_attr(nodes, attr):
    return [node for node in nodes if attr in walk_tree(node)]


def walk_tree(node):
    try:
        d = node.__dict__
    except AttributeError:
        d = {}
        yield node
    for key, value in d.items():
        if isinstance(value, list):
            for val in value:
                for _ in ast.walk(val):
                    yield _
        elif issubclass(type(value), ast.AST):
            for _ in walk_tree(value):
                yield _
        else:
            yield value


def convert_to_python(ast_source):
    """
    Converts the ast objects back into human readable Python code
    """
    return map(codegen.to_source, ast_source)