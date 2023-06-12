from django.conf import settings
from django.db import models
from django.utils import timezone

from ..utils import generate_hash, get_api_key


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
    def get_user_by_key(key):
        hashed_key = generate_hash(key)
        try:
            api_key = APIKey.objects.get(
                active=True, key=hashed_key, profile__user__is_active=True
            )
        except APIKey.DoesNotExist:
            return None

        api_key.last_used = timezone.now()
        api_key.save()

        return api_key.profile.user

    def save(self, *args, **kwargs):
        if not self.key:
            api_key, hashed_key = get_api_key()
            self.key = hashed_key
            self._api_key = api_key
        return super().save(*args, **kwargs)
