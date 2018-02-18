import os

from django.core.files.storage import default_storage

from .. import settings as wooey_settings


def get_subparser_form_slug(script_version, slug):
    return script_version.scriptparameter_set.get(script_param=slug).form_slug

def save_script_path(script_path):
    filename = os.path.split(script_path)[1]
    filename = os.path.join(wooey_settings.WOOEY_SCRIPT_DIR, filename)
    return default_storage.save(filename, open(script_path))
