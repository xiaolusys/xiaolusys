# coding: utf8
from __future__ import absolute_import, unicode_literals

class XiaoluPayException(BaseException):
    pass

class ChannelNotCompleteException(XiaoluPayException):
    pass