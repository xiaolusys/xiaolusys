
import os
from django.conf import settings
from django import template

register = template.Library()

@register.simple_tag
def font_path(fontname):
    return os.path.join(settings.BASE_FONT_PATH , fontname)