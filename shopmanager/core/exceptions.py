
class WeixinPubCertificateMissException(Exception):
    
    def __str__(self):
        return u'微信授权错误：%s'%(self.message)