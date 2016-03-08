from __future__ import division, absolute_import
from django import template
from django.utils.safestring import mark_safe
from django.contrib.contenttypes.models import ContentType
from django.template.base import TemplateSyntaxError

from inspect import getargspec
import hashlib

from six.moves.urllib_parse import urlencode

from .. import settings as wooey_settings
from ..django_compat import TagHelperNode, parse_bits
from ..version import DJANGO_VERSION, DJ19


class Library(template.Library):
    if DJANGO_VERSION >= DJ19:
        simple_assignment_tag = template.Library.simple_tag
    else:
        def simple_assignment_tag(self, func=None, takes_context=None, name=None):
            '''
            Like assignment_tag but when "as" not provided, falls back to simple_tag behavior!
            NOTE: this is based on Django's assignment_tag implementation, modified as needed.

            https://gist.github.com/natevw/f14812604be62c073461
            '''
            # (nvw) imports necessary to match original context

            def dec(func):
                params, varargs, varkw, defaults = getargspec(func)

                # (nvw) added from Django's simple_tag implementation
                class SimpleNode(TagHelperNode):
                    def render(self, context):
                        resolved_args, resolved_kwargs = self.get_resolved_arguments(context)
                        return func(*resolved_args, **resolved_kwargs)

                class AssignmentNode(TagHelperNode):
                    def __init__(self, takes_context, args, kwargs, target_var):
                        super(AssignmentNode, self).__init__(takes_context, args, kwargs)
                        self.target_var = target_var

                    def render(self, context):
                        resolved_args, resolved_kwargs = self.get_resolved_arguments(context)
                        context[self.target_var] = func(*resolved_args, **resolved_kwargs)
                        return ''

                function_name = (name or
                    getattr(func, '_decorated_function', func).__name__)

                def compile_func(parser, token):
                    bits = token.split_contents()[1:]
                    if len(bits) > 2 and bits[-2] == 'as':
                        target_var = bits[-1]
                        bits = bits[:-2]
                        args, kwargs = parse_bits(parser, bits, params,
                            varargs, varkw, defaults, takes_context, function_name)
                        return AssignmentNode(takes_context, args, kwargs, target_var)
                    else:
                        args, kwargs = parse_bits(parser, bits, params,
                            varargs, varkw, defaults, takes_context, function_name)
                        return SimpleNode(takes_context, args, kwargs)

                compile_func.__doc__ = func.__doc__
                self.tag(function_name, compile_func)
                return func

            if func is None:
                # @register.assignment_tag(...)
                return dec
            elif callable(func):
                # @register.assignment_tag
                return dec(func)
            else:
                raise TemplateSyntaxError("Invalid arguments provided to assignment_tag")

register = Library()


@register.simple_tag
def get_user_favorite_count(user, app, model):
    from ..models import Favorite
    ctype = ContentType.objects.get(app_label=app, model=model)
    # Return the current total number for UI updates
    favorites_count = Favorite.objects.filter(content_type=ctype, user=user).count()
    return str(favorites_count)


@register.simple_assignment_tag
def get_wooey_setting(name):
    return getattr(wooey_settings, name, "")


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


@register.filter
def concat(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)


class GravatarUrlNode(template.Node):
    def __init__(self, email, size):
        self.email = template.Variable(email)
        self.size = template.Variable(size)

    def render(self, context):
        try:
            email = self.email.resolve(context)
        except template.VariableDoesNotExist:
            return ''

        try:
            size = self.size.resolve(context)
        except template.VariableDoesNotExist:
            return ''

        url = "http://www.gravatar.com/avatar/" + hashlib.md5(email.lower().encode()).hexdigest() + "?"
        url += urlencode({'s': str(size)})

        return url


@register.tag
def gravatar(parser, token):
    try:
        tag_name, email, size = token.split_contents()

    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires email and size arguments" % token.contents.split()[0])

    return GravatarUrlNode(email, size)


@register.filter
def get_range(value):
    return range(int(value))


@register.simple_assignment_tag(takes_context=True)
def absolute_url(context, url):
    request = context['request']
    return request.build_absolute_uri(url)
