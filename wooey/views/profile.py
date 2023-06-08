from django.http import HttpResponse, JsonResponse

from ..forms import APIKeyForm, APIKeyIDForm
from ..models import APIKey, WooeyProfile


def requires_login(func):
    def inner(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return HttpResponse(status_code=403)
        return func(request, *args, **kwargs)

    return inner


@requires_login
def toggle_api_key(request):
    user = request.user
    profile, _ = WooeyProfile.objects.get_or_create(user=user)
    form = APIKeyIDForm(request.POST)
    if not form.is_valid():
        return JsonResponse(
            {
                "valid": False,
                "errors": form.errors,
            }
        )
    api_key = APIKey.objects.get(pk=form.cleaned_data["id"], profile=profile)
    api_key.active = not api_key.active
    api_key.save()
    return JsonResponse(
        {
            "id": api_key.id,
            "active": api_key.active,
        }
    )


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


@requires_login
def delete_api_key(request):
    user = request.user
    profile = WooeyProfile.objects.get_or_create(user=user)
    form = APIKeyIDForm(request.POST)
    if not form.is_valid():
        return JsonResponse(
            {
                "valid": False,
                "errors": form.errors,
            }
        )
    api_key = APIKey.objects.get(pk=form.cleaned_data["id"], profile=profile)
    api_key.delete()
    return JsonResponse(
        {
            "id": api_key.id,
        }
    )
