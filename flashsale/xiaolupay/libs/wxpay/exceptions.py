# coding: utf8
from __future__ import absolute_import, unicode_literals

class WxPayException(Exception):
    '''Base Alipay Exception'''


class WxPayMissingParameter(WxPayException):
    """Raised when the create payment url process is missing some
    parameters needed to continue"""


class WxPayParameterValueError(WxPayException):
    """Raised when parameter value is incorrect"""


class WxPayTokenAuthorizationError(WxPayException):
    '''The error occurred when getting token '''

class WxPayAPIError(WxPayException):
    '''The error occurred when getting token '''