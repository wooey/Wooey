from django.http import JsonResponse
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .. import models
from ..utils import requires_login


@csrf_exempt
@require_http_methods(["GET"])
@requires_login
def job_status(request, job_id):
    job = models.WooeyJob.objects.get(id=job_id)
    if job.can_user_view(request.user):
        return JsonResponse(
            {
                "status": job.status,
                "is_complete": job.status in models.WooeyJob.TERMINAL_STATES,
            }
        )
    else:
        return JsonResponse(
            {
                "valid": False,
                "errors": {
                    "__all__": [
                        force_str(_("You are not permitted to access this job."))
                    ]
                },
            },
            status=403,
        )


@csrf_exempt
@require_http_methods(["GET"])
@requires_login
def job_details(request, job_id):
    job = models.WooeyJob.objects.get(id=job_id)
    if job.can_user_view(request.user):
        assets = []
        is_terminal = job.status in models.WooeyJob.TERMINAL_STATES
        if is_terminal:
            for asset in job.userfile_set.all():
                assets.append(
                    {
                        "name": asset.filename,
                        "url": request.build_absolute_uri(
                            asset.system_file.filepath.url
                        ),
                    }
                )
        return JsonResponse(
            {
                "status": job.status,
                "is_complete": is_terminal,
                "uuid": job.uuid,
                "job_name": job.job_name,
                "job_description": job.job_description,
                "stdout": job.stdout,
                "stderr": job.stderr,
                "assets": assets,
            }
        )
    else:
        return JsonResponse(
            {
                "valid": False,
                "errors": {
                    "__all__": [
                        force_str(_("You are not permitted to access this job."))
                    ]
                },
            },
            status=403,
        )
