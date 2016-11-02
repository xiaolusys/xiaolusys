
import os

from django import template
from django.template.base import Node
from django.utils.safestring import mark_safe

class SessionTokenNone(Node):
    def render(self, context):
        session_token = context.get('sessionid', None)
        if session_token:
            if session_token == 'NOTPROVIDED':
                return mark_safe(u"")
            else:
                return mark_safe(u"<div style='display:none'><input type='hidden' name='sessionid' value='%s' /></div>" % session_token)
        else:
            print 'session_token:',session_token
            # It's very probable that the token is missing because of
            # misconfiguration, so we raise a warning
            from django.conf import settings
            if settings.DEBUG:
                import warnings
                warnings.warn("A {% session_token %} was used in a template, but the context did not provide the value.  This is usually caused by not using RequestContext.")
            return u''
    
register = template.Library()

@register.simple_tag
def font_path(fontname):
    from django.conf import settings
    return os.path.join(settings.BASE_FONT_PATH , fontname)

@register.tag
def session_token(parser, token):
    snode = SessionTokenNone()
    return snode