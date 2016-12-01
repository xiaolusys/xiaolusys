# coding: utf8
from __future__ import absolute_import, unicode_literals

import unittest
import six
from xml.etree import ElementTree
if six.PY3:
    from urllib.parse import parse_qs, urlparse
else:
    from urlparse import parse_qs, urlparse


class AlipayTests(unittest.TestCase):

    def Alipay(self, *a, **kw):
        from .app import AliPay
        return AliPay(*a, **kw)


    def setUp(self):
        self.alipay = self.Alipay(pid='pid', key='key', seller_email='lxneng@gmail.com')


