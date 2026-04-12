from functools import wraps
import json

from django.http import JsonResponse, QueryDict
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _


def login_required_response():
    return JsonResponse(
        {
            "valid": False,
            "errors": {
                "__all__": [force_str(_("Must be authenticated to use this method."))]
            },
        },
        status=403,
    )


def requires_login(func):
    @wraps(func)
    def inner(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return login_required_response()
        return func(request, *args, **kwargs)

    return inner


def requires_staff(func):
    @wraps(func)
    def inner(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return login_required_response()
        if not user.is_staff:
            return JsonResponse(
                {
                    "valid": False,
                    "errors": {
                        "__all__": [
                            force_str(
                                _("You do not have permission to manage scripts.")
                            )
                        ]
                    },
                },
                status=403,
            )
        return func(request, *args, **kwargs)

    return inner


def get_submitted_data(request):
    content_type = request.headers.get("Content-Type", "").lower()
    if "application/json" in content_type:
        body = request.body.decode("utf-8") if request.body else "{}"
        return json.loads(body or "{}")
    if request.method == "PATCH":
        return QueryDict(request.body).dict()
    return request.POST.dict()
