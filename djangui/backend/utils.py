__author__ = 'chris'

def sanitize_name(name):
    return name.replace(' ', '_').replace('-','_')

def sanitize_string(value):
    return value.replace('"', '\\"')