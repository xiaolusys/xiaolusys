# coding: utf8
from __future__ import absolute_import, unicode_literals

class AliPayException(Exception):
    '''Base AliPay Exception'''

    def __init__(self, message='', fail_code='', fail_msg='', *args, **kwargs):
        self.fail_code = fail_code
        self.fail_msg  = fail_msg
        self.message   = message

    def __unicode__(self):
        return '%s(%s: %s)'%(self.message, self.fail_code, self.fail_msg)


class AliPayMissingParameter(AliPayException):
    """Raised when the create payment url process is missing some
    parameters needed to continue"""


class AliPayParameterValueError(AliPayException):
    """Raised when parameter value is incorrect"""


class AliPayTokenAuthorizationError(AliPayException):
    '''The error occurred when getting token '''

class AliPayAPIError(AliPayException):
    '''The error occurred when getting token '''

class AliPayAPIResponseError(AliPayException):
    '''The error occurred when getting token '''