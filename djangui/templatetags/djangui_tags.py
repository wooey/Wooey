from __future__ import division
from django import template

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