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
    from ..models import Group
    groups = obj.user_groups
    if not groups and obj.is_active:
        return True
    if obj.is_active is True:
        if not isinstance(groups, list):
            groups = [groups]
        if user.groups.filter(name__in=groups).exists():
            return True
    return 'disabled' if djangui_settings.DJANGUI_SHOW_LOCKED_SCRIPTS else 'hide'
