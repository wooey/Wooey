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

from .. import errors, models
from .. import settings as wooey_settings
from ..backend import utils
from .forms import (
    AddScriptForm,
    ScriptPatchForm,
    ScriptVersionPatchForm,
    SubmitForm,
)
from .utils import get_submitted_data, requires_login, requires_staff


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


def _get_script_or_error(slug):
    try:
        return (
            models.Script.objects.select_related(
                "script_group", "virtual_environment"
            ).get(slug=slug),
            None,
        )
    except models.Script.DoesNotExist:
        return None, JsonResponse(
            {
                "valid": False,
                "errors": {"script": [force_str(_("Unable to find script."))]},
            },
            status=404,
        )


def _serialize_script_version(script_version):
    return {
        "id": script_version.id,
        "script_version": script_version.script_version,
        "script_iteration": script_version.script_iteration,
        "is_active": script_version.is_active,
        "default_version": script_version.default_version,
        "checksum": script_version.checksum,
        "script_path": script_version.script_path.name,
        "script_url": script_version.script_path.url,
        "script_filename": os.path.basename(script_version.script_path.name),
        "created_date": script_version.created_date,
        "created_by": _serialize_user(script_version.created_by),
        "modified_date": script_version.modified_date,
        "modified_by": _serialize_user(script_version.modified_by),
    }


def _get_script_issues(script):
    issues = []
    version_count = script.script_version.count()
    active_versions = script.script_version.filter(is_active=True)
    default_versions = active_versions.filter(default_version=True).count()

    if version_count == 0:
        issues.append(force_str(_("This script does not have any script versions.")))
    elif active_versions.count() == 0:
        issues.append(
            force_str(_("This script does not have any active script versions."))
        )
    if version_count and default_versions == 0:
        issues.append(force_str(_("This script does not have a default version.")))
    elif default_versions > 1:
        issues.append(force_str(_("This script has multiple default versions.")))

    return issues


def _serialize_user(user):
    if not user:
        return ""
    return user.get_full_name() or user.username


def _serialize_script(script, include_versions=False):
    versions_qs = script.script_version.all().order_by("-created_date", "-pk")
    default_version = versions_qs.filter(default_version=True, is_active=True).first()
    data = {
        "id": script.id,
        "slug": script.slug,
        "script_name": script.script_name,
        "group": script.script_group.group_name if script.script_group else "",
        "group_slug": script.script_group.slug if script.script_group else "",
        "virtual_environment_id": script.virtual_environment_id,
        "virtual_environment_name": (
            script.virtual_environment.name if script.virtual_environment else ""
        ),
        "script_description": script.script_description or "",
        "documentation": script.documentation or "",
        "script_order": script.script_order,
        "is_active": script.is_active,
        "ignore_bad_imports": script.ignore_bad_imports,
        "execute_full_path": script.execute_full_path,
        "save_path": script.save_path or "",
        "created_date": script.created_date,
        "created_by": _serialize_user(script.created_by),
        "modified_date": script.modified_date,
        "modified_by": _serialize_user(script.modified_by),
        "versions_count": versions_qs.count(),
        "issues": _get_script_issues(script),
        "default_version": (
            _serialize_script_version(default_version) if default_version else None
        ),
    }
    if include_versions:
        data["versions"] = [_serialize_script_version(i) for i in versions_qs]
    return data


def _update_script_metadata(script, updates):
    updated_fields = []

    if "script_name" in updates:
        script.script_name = updates["script_name"]
        updated_fields.append("script_name")
    if "group" in updates:
        group_name = updates["group"] or wooey_settings.WOOEY_DEFAULT_SCRIPT_GROUP
        script.script_group, _ = models.ScriptGroup.objects.get_or_create(
            group_name=group_name
        )
        updated_fields.append("script_group")
    if "virtual_environment" in updates:
        script.virtual_environment = updates["virtual_environment"]
        updated_fields.append("virtual_environment")
    if "script_description" in updates:
        script.script_description = updates["script_description"]
        updated_fields.append("script_description")
    if "documentation" in updates:
        script.documentation = updates["documentation"]
        updated_fields.append("documentation")
    if "script_order" in updates:
        script.script_order = updates["script_order"]
        updated_fields.append("script_order")
    if "is_active" in updates:
        script.is_active = updates["is_active"]
        updated_fields.append("is_active")
    if "ignore_bad_imports" in updates:
        script.ignore_bad_imports = updates["ignore_bad_imports"]
        updated_fields.append("ignore_bad_imports")
    if "execute_full_path" in updates:
        script.execute_full_path = updates["execute_full_path"]
        updated_fields.append("execute_full_path")
    if "save_path" in updates:
        script.save_path = updates["save_path"] or None
        updated_fields.append("save_path")

    if updated_fields:
        script.save(update_fields=updated_fields)

    return script


def _update_script_audit(script, user):
    if script.created_by_id is None:
        script.created_by = user
    script.modified_by = user
    script.save(update_fields=["created_by", "modified_by", "modified_date"])


def _update_script_version_audit(script_version, user):
    if script_version.created_by_id is None:
        script_version.created_by = user
    script_version.modified_by = user
    script_version.save(update_fields=["created_by", "modified_by", "modified_date"])


@csrf_exempt
@require_http_methods(["GET"])
@requires_staff
def list_scripts(request):
    scripts = (
        models.Script.objects.select_related("script_group", "virtual_environment")
        .prefetch_related("script_version")
        .order_by("script_name", "pk")
    )
    return JsonResponse(
        {"valid": True, "scripts": [_serialize_script(script) for script in scripts]}
    )


@csrf_exempt
@require_http_methods(["GET"])
@requires_staff
def script_detail(request, slug):
    script, error = _get_script_or_error(slug)
    if error:
        return error

    return JsonResponse({"valid": True, "script": _serialize_script(script, True)})


@csrf_exempt
@require_http_methods(["PATCH"])
@requires_staff
def patch_script(request, slug):
    script, error = _get_script_or_error(slug)
    if error:
        return error

    form = ScriptPatchForm(get_submitted_data(request))
    if not form.is_valid():
        return JsonResponse({"valid": False, "errors": form.errors}, status=400)

    _update_script_metadata(script, form.cleaned_data)
    _update_script_audit(script, request.user)
    return JsonResponse({"valid": True, "script": _serialize_script(script, True)})


@csrf_exempt
@require_http_methods(["PATCH"])
@requires_staff
def patch_script_version(request, slug, version_id):
    try:
        script_version = models.ScriptVersion.objects.select_related("script").get(
            pk=version_id, script__slug=slug
        )
    except models.ScriptVersion.DoesNotExist:
        return JsonResponse(
            {
                "valid": False,
                "errors": {
                    "script_version": [force_str(_("Unable to find script version."))]
                },
            },
            status=404,
        )

    form = ScriptVersionPatchForm(get_submitted_data(request))
    if not form.is_valid():
        return JsonResponse({"valid": False, "errors": form.errors}, status=400)

    updates = form.cleaned_data

    if "default_version" in updates:
        make_default = updates["default_version"]
        if make_default:
            if not script_version.is_active:
                return JsonResponse(
                    {
                        "valid": False,
                        "errors": {
                            "default_version": [
                                force_str(
                                    _(
                                        "A disabled script version cannot be set as default."
                                    )
                                )
                            ]
                        },
                    },
                    status=400,
                )
            models.ScriptVersion.objects.filter(script=script_version.script).exclude(
                pk=script_version.pk
            ).update(default_version=False)
            script_version.default_version = True
            script_version.save()
        else:
            disabling_version = "is_active" in updates and updates["is_active"] is False
            other_defaults = models.ScriptVersion.objects.filter(
                script=script_version.script, default_version=True, is_active=True
            ).exclude(pk=script_version.pk)
            if not other_defaults.exists() and not disabling_version:
                return JsonResponse(
                    {
                        "valid": False,
                        "errors": {
                            "default_version": [
                                force_str(_("A script must have a default version."))
                            ]
                        },
                    },
                    status=400,
                )
            script_version.default_version = False
            script_version.save()

    if "is_active" in updates:
        is_active = updates["is_active"]
        script_version.is_active = is_active
        if not is_active:
            script_version.default_version = False
        script_version.save()

    _update_script_version_audit(script_version, request.user)
    _update_script_audit(script_version.script, request.user)
    return JsonResponse(
        {
            "valid": True,
            "version": _serialize_script_version(script_version),
            "script": _serialize_script(script_version.script, True),
        }
    )


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
    qs = models.ScriptVersion.objects.filter(script__slug=slug, is_active=True)
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

            utils.validate_form(
                form=form, data=wooey_form_data, files=files, user=request.user
            )

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
@requires_staff
def add_or_update_script(request):
    files = request.FILES

    form = AddScriptForm(get_submitted_data(request))
    if not form.is_valid():
        return JsonResponse({"valid": False, "errors": form.errors}, status=400)
    if not files:
        return JsonResponse(
            {
                "valid": False,
                "errors": {"script_file": [force_str(_("A script file is required."))]},
            },
            status=400,
        )

    data = form.cleaned_data
    group = data.get("group")
    set_default_version = data.get("default", True)
    ignore_bad_imports = data.get("ignore_bad_imports")
    metadata_updates = dict(data)
    metadata_updates.pop("default", None)

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
            "set_default_version": set_default_version,
            "ignore_bad_imports": ignore_bad_imports,
        }
        results = utils.add_wooey_script(**add_kwargs)
        output = {
            "script": script_name,
            "success": results["valid"],
            "errors": results["errors"],
        }
        if results["valid"]:
            script = results["script"].script
            _update_script_metadata(script, metadata_updates)
            _update_script_audit(script, request.user)
            _update_script_version_audit(results["script"], request.user)
            results["script"].refresh_from_db()
            output["version"] = results["script"].script_version
            output["iteration"] = results["script"].script_iteration
            output["is_default"] = results["script"].default_version
            output["id"] = script.id
            output["slug"] = script.slug
        response.append(output)

    return JsonResponse(response, safe=False, encoder=errors.WooeyJSONEncoder)
