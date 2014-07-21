#-*- coding:utf8 -*-

class JDRequestException(Exception):

    def __init__(self,code='',msg='',sub_code='',sub_msg=''):
        self.code      = code
        self.message   = msg
        self.sub_code  = sub_code
        self.sub_msg   = sub_msg


    def __str__(self):
        return '(%s,%s,%s,%s)'%(str(self.code),self.message,self.sub_code,self.sub_msg)
    
class JDAuthTokenException(JDRequestException):

    pass



