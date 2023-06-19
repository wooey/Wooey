import hashlib

from django.http import HttpResponse
from django.utils.crypto import get_random_string


def get_api_key():
    api_key = get_random_string(32)
    return api_key, generate_hash(api_key)


def generate_hash(value):
    hasher = hashlib.sha256()
    hasher.update(value.encode("utf-8"))
    return hasher.hexdigest()


def requires_login(func):
    def inner(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return HttpResponse("Must be authenticated to use this method.", status=403)
        return func(request, *args, **kwargs)

    return inner
