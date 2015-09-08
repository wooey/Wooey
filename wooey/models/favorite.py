from django.db import models
from django.conf import settings
from ..django_compat import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Favorite(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='favorites', blank=True, null=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id', )
