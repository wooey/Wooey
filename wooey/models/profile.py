from django.conf import settings
from django.contrib.auth import hashers
from django.db import models


__all__ = ["WooeyProfile", "APIKey"]


class WooeyProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )


class APIKey(models.Model):
    profile = models.ForeignKey("WooeyProfile", on_delete=models.CASCADE, db_index=True)
    name = models.TextField()
    active = models.BooleanField(default=True)
    key = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

    @staticmethod
    def get_user_by_key(user, key):
        for api_key in APIKey.objects.filter(profile__user=user, active=True):
            if hashers.check_password(key, api_key.key):
                return api_key.profile.user
