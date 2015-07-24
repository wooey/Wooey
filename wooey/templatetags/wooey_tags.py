from __future__ import division, absolute_import
from django import template
from .. import settings as wooey_settings
from django.utils.safestring import mark_safe
from django.contrib.contenttypes.models import ContentType

register = template.Library()
@register.filter
def divide(value, arg):
    try:
        return float(value)/float(arg)
    except ZeroDivisionError:
        return None

@register.filter
def endswith(value, arg):
    return str(value).endswith(arg)

@register.filter
def valid_user(obj, user):
    from ..backend import utils
    valid = utils.valid_user(obj, user)
    return True if valid.get('valid') else valid.get('display')

@register.filter
def complete_job(status):
    from ..models import WooeyJob
    from celery import states
    return status in (WooeyJob.COMPLETED, states.REVOKED)

@register.filter
def numericalign(s):
    """
    Takes an input string of "number units" splits it
    and outputs it with each half wrapped in 50% width
    span. Has the effect of centering numbers on the unit part.
    :param s:
    :return: s
    """
    print(s)
    number, units = s.split()
    return mark_safe('<span class="numericalign numericpart">%s</span><span class="numericalign">&nbsp;%s</span>' % (number, units))


@register.filter
def app_model_id(obj):
    """
    Returns a app-model-id string for a given object
    :param obj:
    :return:
    """
    ct = ContentType.objects.get_for_model(obj)

    return '%s-%s-%s' % (ct.app_label, ct.model, obj.id)
