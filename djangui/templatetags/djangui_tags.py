from __future__ import division
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
    return utils.valid_user(obj, user)
