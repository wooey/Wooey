from django.http import JsonResponse
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .. import models
from .forms import VirtualEnvironmentCreateForm, VirtualEnvironmentPatchForm
from .utils import get_submitted_data, requires_staff


def _serialize_virtual_environment(virtual_environment):
    return {
        "id": virtual_environment.id,
        "name": virtual_environment.name,
        "python_binary": virtual_environment.python_binary,
        "requirements": virtual_environment.requirements or "",
        "venv_directory": virtual_environment.venv_directory,
        "install_path": virtual_environment.get_install_path(),
    }


def _get_virtual_environment_or_error(virtual_environment_id):
    try:
        return (
            models.VirtualEnvironment.objects.get(pk=virtual_environment_id),
            None,
        )
    except models.VirtualEnvironment.DoesNotExist:
        return None, JsonResponse(
            {
                "valid": False,
                "errors": {
                    "virtual_environment": [
                        force_str(_("Unable to find virtual environment."))
                    ]
                },
            },
            status=404,
        )


@csrf_exempt
@require_http_methods(["GET"])
@requires_staff
def list_virtual_environments(request):
    virtual_environments = models.VirtualEnvironment.objects.order_by("name", "pk")
    return JsonResponse(
        {
            "valid": True,
            "virtual_environments": [
                _serialize_virtual_environment(virtual_environment)
                for virtual_environment in virtual_environments
            ],
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
@requires_staff
def create_virtual_environment(request):
    form = VirtualEnvironmentCreateForm(get_submitted_data(request))
    if not form.is_valid():
        return JsonResponse({"valid": False, "errors": form.errors}, status=400)

    virtual_environment = models.VirtualEnvironment.objects.create(**form.cleaned_data)
    return JsonResponse(
        {
            "valid": True,
            "virtual_environment": _serialize_virtual_environment(virtual_environment),
        }
    )


@csrf_exempt
@require_http_methods(["PATCH"])
@requires_staff
def patch_virtual_environment(request, virtual_environment_id):
    virtual_environment, error = _get_virtual_environment_or_error(
        virtual_environment_id
    )
    if error:
        return error

    form = VirtualEnvironmentPatchForm(get_submitted_data(request))
    if not form.is_valid():
        return JsonResponse({"valid": False, "errors": form.errors}, status=400)

    for field_name, value in form.cleaned_data.items():
        setattr(virtual_environment, field_name, value)
    virtual_environment.save()

    return JsonResponse(
        {
            "valid": True,
            "virtual_environment": _serialize_virtual_environment(virtual_environment),
        }
    )
