
class TaobaoRequestException(Exception):

    def __init__(self,code=None,msg=None,sub_code=None,sub_msg=None):
        self.code = code
        self.msg  = msg
        self.sub_code  = sub_code
        self.sub_msg   = sub_msg

    def __str__(self):
        return '(%s,%s,%s,%s)'%(str(self.code),self.msg,self.sub_code,self.sub_msg)



class APIConnectionTimeOutException(TaobaoRequestException):
    """
    {'code': 520,
     'msg': u'Remote service error',
     'sub_code': u'isp.remote-service-timeout',
     'sub_msg': u'API\u8c03\u7528\u670d\u52a1\u8d85\u65f6'}
    """



class RemoteConnectionException(TaobaoRequestException):
    """
    {'code': 520,
    'msg': u'Remote service error',
    'sub_code': u'isp.remote-connection-error',
    'sub_msg': u'API\u8c03\u7528\u8fdc\u7a0b\u8fde\u63a5\u9519\u8bef'}
    """



class ServiceRejectionException(TaobaoRequestException):
    """
    {'code': 520,
     'msg': u'Remote service error',
     'sub_code': u'isv.trade-service-rejection',
     'sub_msg': u'\u8d85\u65f6\u8bf7\u6c42\u8fc7\u591a\uff0c\u8bf7\u5c06\u67e5\u8be2\u65f6\u95f4\u95f4\u9694\u7f29\u77ed,3\u5206\u949f\u540e\u518d\u67e5\u8be2\uff01'}
    """



class UserFenxiaoUnuseException(TaobaoRequestException):
    """
    {'code': 670,
    'msg': u'Remote service error',
    'sub_code': u'isv.invalid-parameter:user_id_num',
    'sub_msg': u'\u7528\u6237\u6570\u5b57ID\u4e0d\u5408\u6cd5\uff0c\u6216\u8005\u4e0d\u662f\u5206\u9500\u5e73\u53f0\u7528\u6237'}
    {u'code': 15,
     u'msg': u'Remote service error',
     u'sub_code': u'isv.invalid-parameter:user_id_num',
     u'sub_msg': u'\u7528\u6237\u6570\u5b57ID\u4e0d\u5408\u6cd5\uff0c\u6216\u8005\u4e0d\u662f\u5206\u9500\u5e73\u53f0\u7528\u6237'}
    """

class InsufficientIsvPermissionsException(TaobaoRequestException):
    """
    {'code': 670,
    'msg': u'Remote service error',
    'sub_code': u'isv.invalid-parameter:user_id_num',
    'sub_msg': u'\u7528\u6237\u6570\u5b57ID\u4e0d\u5408\u6cd5\uff0c\u6216\u8005\u4e0d\u662f\u5206\u9500\u5e73\u53f0\u7528\u6237'}
    {u'code': 15,
     u'msg': u'Remote service error',
     u'sub_code': u'isv.invalid-parameter:user_id_num',
     u'sub_msg': u'\u7528\u6237\u6570\u5b57ID\u4e0d\u5408\u6cd5\uff0c\u6216\u8005\u4e0d\u662f\u5206\u9500\u5e73\u53f0\u7528\u6237'}
    """



class AppCallLimitedException(TaobaoRequestException):
    """
    {u'msg': u'App Call Limited', u'sub_code': u'accesscontrol.limited-by-app-access-count',
        u'code': 7, u'sub_msg': u'This ban will last for 31062 more seconds'}
    """

class ContentNotRightException(TaobaoRequestException):
    """
    connect repear or refuse
    """

class SessionExpiredException(TaobaoRequestException):
    """
    connect repear or refuse
    """

