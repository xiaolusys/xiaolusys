# coding: utf8
from __future__ import absolute_import, unicode_literals

class SandpayException(Exception):
    '''Base Sandpay Exception'''

    def __unicode__(self):
        return '未知支付异常: %s' % self.message

class SandpaySystemError(SandpayException):
    ''' ERROR CODE : 00**'''

    def __unicode__(self):
        return '支付系统错误: %s' % self.message

class SandpayMerchVerifyError(SandpayException):
    ''' ERROR CODE : 10**'''

    def __unicode__(self):
        return '商户校验错误: %s' % self.message

class SandpayMsgVerifyError(SandpayException):
    ''' ERROR CODE : 20**'''

    def __unicode__(self):
        return '消息校验错误: %s' % self.message

class SandpayServiceError(SandpayException):
    ''' ERROR CODE : 30**'''

    def __unicode__(self):
        return '业务处理异常: %s' % self.message

