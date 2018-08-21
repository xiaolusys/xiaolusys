# encoding=utf8
import random
import urlparse
from django.conf import settings


def replace_domain(url, domain=None, scheme=None):
    """
    替换url域名
    """
    o = urlparse.urlparse(url)
    if not domain:
        domain, scheme = random.choice(settings.STANDBY_DOMAINS)

    if not scheme:
        scheme = o.scheme

    try:
        n = urlparse.urlunparse((scheme, domain, o.path, o.params, o.query, o.fragment))
    except Exception:
        n = url
    return n