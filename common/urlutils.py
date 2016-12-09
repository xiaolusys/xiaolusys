# encoding=utf8
import random
import urlparse
from django.conf import settings


def replace_domain(url, domain=None):
    """
    替换url域名
    """
    if not domain:
        domain = random.choice(settings.STANDBY_DOMAINS)

    try:
        o = urlparse.urlparse(url)
        n = urlparse.urlunparse((o.scheme, domain, o.path, o.params, o.query, o.fragment))
    except Exception:
        n = url
    return n