# encoding=utf8
import urllib
import urlparse
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def replace_url_params(context, key, value):
    req = context['req']
    url = req.get_full_path()

    url = url.encode('utf8')
    pr = urlparse.urlparse(url)
    query = dict(urlparse.parse_qsl(pr.query))
    query[key] = value
    return urllib.urlencode(query)
