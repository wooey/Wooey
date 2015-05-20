from __future__ import division, absolute_import
from django import template
from .. import settings as djangui_settings

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
    from ..models import DjanguiJob
    from celery import states
    return status in (DjanguiJob.COMPLETED, states.REVOKED)