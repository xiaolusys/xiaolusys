# coding:utf-8
    
class WeixinAutherizeFail(Exception):
    
    def __str__(self):
        return u'微信授权错误：{}'.format(self.message)