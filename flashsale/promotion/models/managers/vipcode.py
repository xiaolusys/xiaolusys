# coding=utf-8
import string
import random
from core.managers import BaseManager

CHARANGE_STR = string.ascii_lowercase
NUMBER_STR = '0123456789'


class VipCodeManager(BaseManager):
    def get_queryset(self):
        super_tm = super(VipCodeManager, self)
        return super_tm.get_queryset()

    def genCode(self):
        """ 生成邀请码 """
        xx = random.randint(1000000, 9999999)
        return str(xx)

    def genVIpCode(self, mobile, expiried):
        new_code = self.genCode()
        cnt = 0
        while True:
            cnt += 1
            try:
                xl_invite_code = self.get(vipcode=new_code)
            except self.model.DoesNotExist:
                try:
                    self.create(vipcode=new_code, mobile=mobile, expiried=expiried)
                except:
                    new_code = self.genCode()
                else:
                    return new_code
            else:
                return xl_invite_code.vipcode
            if cnt > 20:
                raise Exception(u'邀请码生成异常')
