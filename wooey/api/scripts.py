import argparse
import json
import os
import shlex
from itertools import groupby

from django.http import JsonResponse
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .. import models
from ..backend import utils
from .forms import AddScriptForm, SubmitForm
from ..utils import requires_login
from .. import settings as wooey_settings


def create_argparser(script_version):
    """From a script version, return an argparse cli

    This is meant to assist in processing a command sent to the Wooey API for
    running a script. This is an attempt at a shortcut instead of building
    our own tokenizer and parser. One downside at the moment is we do not
    store alternative parameters that a script can have (e.g. if `--foo` can also
    be specified as `--old-foo`). So if a user enters the one not saved, it will
    be an error.
    """
    parser = argparse.ArgumentParser(prog="wooey-temp")
    subparsers = None
    parameters = list(script_version.get_parameters())
    grouped_parameters = {
        subparser: list(arguments)
        for subparser, arguments in groupby(
            sorted(parameters, key=lambda x: [x.parser.name, x.param_order]),
            key=lambda x: x.parser.name,
        )
    }

    def log_error(parser):
        error_func = parser.error

        def inner(message):
            parser._wooey_error = message
            return error_func(message)

        return inner

    parser.error = log_error(parser)

    for subparser_name, arguments in grouped_parameters.items():
        if subparser_name:
            if not subparsers:
                subparsers = parser.add_subparsers(dest="wooey_subparser")
            active_parser = subparsers.add_parser(subparser_name)
        else:
            active_parser = parser
        for argument in arguments:
            argument_kwargs = {"dest": argument.form_slug, "default": argument.default}
            if argument.multiple_choice:
                argument_kwargs["nargs"] = "*"
            if argument.short_param:
                argument_kwargs["required"] = argument.required
                active_parser.add_argument(argument.short_param, **argument_kwargs)
            else:
                active_parser.add_argument(**argument_kwargs)
    return parser


@csrf_exempt
@require_http_methods(["POST"])
@requires_login
def submit_script(request, slug=None):
    if "application/json" in request.headers.get("Content-Type", "").lower():
        submitted_data = json.loads(request.body)
    else:
        submitted_data = request.POST
    files = request.FILES

    form = SubmitForm(submitted_data)
    if not form.is_valid():
        return JsonResponse({"valid": False, "errors": form.errors})
    data = form.cleaned_data

    version = data["version"]
    iteration = data["iteration"]
    command = data["command"]
    qs = models.ScriptVersion.objects.filter(script__slug=slug)
    if not version and not iteration:
        qs = qs.filter(default_version=True)
    else:
        if version:
            qs = qs.filter(script_version=version)
        if iteration:
            qs = qs.filter(script_iteration=iteration)
    try:
        script_version = qs.get()
    except models.ScriptVersion.DoesNotExist:
        return JsonResponse(
            {"valid": False, "errors": {"script": _("Unable to find script.")}}
        )

    valid = utils.valid_user(script_version.script, request.user).get("valid")
    if valid:
        group_valid = utils.valid_user(
            script_version.script.script_group, request.user
        )["valid"]

        parser = create_argparser(script_version)
        try:
            parsed_command = parser.parse_args(shlex.split(command))
        except SystemExit:
            return JsonResponse(
                {"valid": False, "errors": {"command": parser._wooey_error}}, status=400
            )
        if valid and group_valid:
            job_data = vars(parsed_command)
            job_data["job_name"] = data["job_name"]
            if data["job_description"]:
                job_data["job_description"] = data["job_description"]
            subparser_id = script_version.scriptparser_set.get(
                name=job_data.pop("wooey_subparser", "")
            ).id
            form = utils.get_master_form(
                script_version=script_version, parser=subparser_id
            )
            wooey_form_data = job_data.copy()
            wooey_form_data["wooey_type"] = script_version.pk

            # We need to remap uploaded files to the correct slug
            form_slugs = list(wooey_form_data)
            for form_slug in form_slugs:
                form_value = wooey_form_data[form_slug]
                if isinstance(form_value, list):
                    to_append = []
                    for index, value in enumerate(form_value):
                        if value in files:
                            to_append.append(index)
                    if to_append:
                        existing_files = files.get(form_slug, [])
                        files.setlist(
                            form_slug,
                            utils.flatten(
                                existing_files
                                + [files.pop(form_value[i]) for i in to_append]
                            ),
                        )
                        for index in reversed(to_append):
                            form_value.pop(index)
                else:
                    if form_value in files:
                        files.setlist(form_slug, files.pop(form_value))
                        wooey_form_data[form_slug] = [""]

            utils.validate_form(form=form, data=wooey_form_data, files=files)

            if not form.errors:
                job = utils.create_wooey_job(
                    script_parser_pk=subparser_id,
                    script_version_pk=script_version.id,
                    user=request.user,
                    data=form.cleaned_data,
                )
                job.submit_to_celery()
                return JsonResponse({"valid": True, "job_id": job.id})
            else:
                return JsonResponse({"valid": False, "errors": form.errors}, status=400)
    else:
        return JsonResponse(
            {
                "valid": False,
                "errors": {
                    "script": [
                        force_str(_("You are not permitted to access this script."))
                    ]
                },
            },
            status=403,
        )


@csrf_exempt
@require_http_methods(["POST"])
@requires_login
def add_or_update_script(request):
    submitted_data = request.POST.dict()
    files = request.FILES

    form = AddScriptForm(submitted_data)
    if not form.is_valid():
        return JsonResponse({"valid": False, "errors": form.errors})

    data = form.cleaned_data
    group = data["group"] or wooey_settings.WOOEY_DEFAULT_SCRIPT_GROUP

    response = []

    for script_name, script_file in files.items():
        script_path = utils.default_storage.save(
            os.path.join(wooey_settings.WOOEY_SCRIPT_DIR, script_file.name),
            script_file,
        )
        if wooey_settings.WOOEY_EPHEMERAL_FILES:
            # save it locally as well (the default_storage will default to the remote store)
            script_file.seek(0)
            local_storage = utils.get_storage(local=True)
            local_storage.save(
                os.path.join(
                    wooey_settings.WOOEY_SCRIPT_DIR,
                    script_file.name,
                ),
                script_file,
            )
        add_kwargs = {
            "script_path": script_path,
            "group": group,
            "script_name": script_name,
            "set_default_version": data["default"],
            "ignore_bad_imports": data["ignore_bad_imports"],
        }
        results = utils.add_wooey_script(**add_kwargs)
        output = {
            "script": script_name,
            "success": results["valid"],
            "errors": results["errors"],
        }
        if results["valid"]:
            output["version"] = results["script"].script_version
            output["iteration"] = results["script"].script_iteration
            output["is_default"] = results["script"].default_version
        response.append(output)

    return JsonResponse(response, safe=False)
