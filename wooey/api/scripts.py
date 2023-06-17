import argparse
import json
import shlex
from itertools import groupby

from django.http import JsonResponse
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .. import models
from ..backend import utils
from .forms import SubmitForm


def create_argparser(script_version):
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
    for subparser_name, arguments in grouped_parameters.items():
        if subparser_name:
            if not subparsers:
                subparsers = parser.add_subparsers(dest="wooey_subparser")
            active_parser = subparsers.add_parser(subparser_name)
        else:
            active_parser = parser
        for argument in arguments:
            argument_kwargs = {"dest": argument.form_slug}
            active_parser.add_argument(argument.short_param, **argument_kwargs)
    return parser


@csrf_exempt
@require_http_methods(["POST"])
def submit_script(request, slug=None):
    if request.POST:
        submitted_data = request.POST.dict()
        files = request.FILES
    else:
        submitted_data = json.loads(request.body.decode("utf-8"))
        files = None
    form = SubmitForm(submitted_data)
    if not form.is_valid():
        return JsonResponse({"valid": False, "errors": form.errors})
    data = form.cleaned_data

    version = data["version"]
    iteration = data["iteration"]
    command = data["command"]
    qs = models.ScriptVersion.objects.filter(script__slug=slug)
    if not version and not iteration:
        script_version = qs.latest()
    else:
        if version:
            qs = qs.filter(script_version=version)
        if iteration:
            qs = qs.filter(script_iteration=iteration)
        script_version = qs.get()

    valid = utils.valid_user(script_version.script, request.user).get("valid")
    if valid:
        group_valid = utils.valid_user(
            script_version.script.script_group, request.user
        )["valid"]

        parser = create_argparser(script_version)
        parsed_command = parser.parse_args(shlex.split(command))
        if valid and group_valid:
            job_data = vars(parsed_command)
            job_data["job_name"] = data["job_name"]
            subparser_id = script_version.scriptparser_set.get(
                name=job_data.pop("wooey_subparser")
            ).id
            form = utils.get_master_form(
                script_version=script_version, parser=subparser_id
            )
            wooey_form_data = job_data.copy()
            wooey_form_data["wooey_type"] = script_version.pk
            utils.validate_form(form=form, data=wooey_form_data, files=files)

            if not form.errors:
                job = utils.create_wooey_job(
                    script_parser_pk=subparser_id,
                    script_version_pk=script_version.id,
                    user=request.user,
                    data=job_data,
                )
                job.submit_to_celery()
                return JsonResponse({"valid": True, "job_id": job.id})
            else:
                return {"valid": False, "errors": form.errors}
    else:
        return {
            "valid": False,
            "errors": {
                "__all__": [
                    force_str(_("You are not permitted to access this script."))
                ]
            },
        }

    return JsonResponse(
        {
            "valid": False,
            "errors": {
                "__all__": [
                    force_str(_("You are not permitted to access this script."))
                ]
            },
        }
    )
