from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods

from ..forms import APIKeyForm
from ..models import APIKey, WooeyProfile
from ..utils import requires_login


@require_http_methods(["POST"])
@requires_login
def toggle_api_key(request, id):
    user = request.user
    profile, _ = WooeyProfile.objects.get_or_create(user=user)
    try:
        api_key = APIKey.objects.get(pk=id, profile=profile)
    except APIKey.DoesNotExist:
        return HttpResponse("API Key not found", status=404)
    api_key.active = not api_key.active
    api_key.save()
    return JsonResponse(
        {
            "id": api_key.id,
            "active": api_key.active,
        }
    )


@require_http_methods(["POST"])
@requires_login
def create_api_key(request):
    user = request.user
    profile, _ = WooeyProfile.objects.get_or_create(user=user)
    form = APIKeyForm(request.POST)
    if form.is_valid():
        api_key = APIKey(
            name=form.cleaned_data["name"],
            profile=profile,
        )
        api_key.save()

        return JsonResponse(
            {
                "id": api_key.id,
                "name": api_key.name,
                "created_date": api_key.created_date,
                "api_key": api_key._api_key,
            }
        )
    else:
        return JsonResponse({"valid": False, "errors": form.errors})


@require_http_methods(["DELETE"])
@requires_login
def delete_api_key(request, id):
    user = request.user
    profile, _ = WooeyProfile.objects.get_or_create(user=user)
    try:
        api_key = APIKey.objects.get(pk=id, profile=profile)
    except APIKey.DoesNotExist:
        return HttpResponse("API Key not found", status=404)
    api_key.delete()
    return JsonResponse(
        {
            "id": api_key.id,
        }
    )
