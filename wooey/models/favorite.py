from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from ..version import DJANGO_VERSION, DJ18

# This cannot be in django_compat due to the other modules which import it prior to application loading.
# We can think about later adding a django_compat_post_load or something to handle these corner cases if more arise
# GenericForeignKey compatibility fixes
if DJANGO_VERSION < DJ18:
    from django.contrib.contenttypes.generic import GenericForeignKey

else:
    from django.contrib.contenttypes.fields import GenericForeignKey


class Favorite(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='favorites', blank=True, null=True, on_delete=models.CASCADE)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id', )
        app_label = 'wooey'
        verbose_name = _('favorite')
        verbose_name_plural = _('favorites')
