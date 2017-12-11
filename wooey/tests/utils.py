def get_subparser_form_slug(script_version, slug):
    return script_version.scriptparameter_set.get(script_param=slug).form_slug
