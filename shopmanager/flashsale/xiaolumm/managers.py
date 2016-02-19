#-*- coding:utf-8 -*-
import random
import datetime
from django.db import models
from django.db.models import Q,Sum
from django.db.models.signals import post_save
from django.db import IntegrityError, transaction
from django.forms.models import model_to_dict


class XiaoluMamaManager(models.Manager):

    def get_queryset(self):

        super_tm = super(XiaoluMamaManager,self)
        #adapt to higer version django(>1.4)
        if hasattr(super_tm,'get_query_set'):
            return super_tm.get_query_set()
        return super_tm.get_queryset()


    def  charge(self,xlmm,user,*args,**kwargs):

        if xlmm.charge_status == self.model.CHARGED:
            return False

        xlmm.manager = user.id
        xlmm.charge_status = self.model.CHARGED
        xlmm.save()

        return True


    def  uncharge(self,xlmm,*args,**kwargs):

        xlmm.charge_status = self.model.UNCHARGE
        xlmm.save()

    @property
    def normal_queryset(self):

        queryset = self.get_queryset()
        return queryset.filter(status=self.model.EFFECT)


class XlmmFansManager(models.Manager):

    def get_queryset(self):
        super_fans = super(XlmmFansManager, self)
        if hasattr(super_fans, 'get_query_set'):
            return super_fans.get_query_set()
        return super_fans.get_queryset()

    def record_fans_num(self, xlmm, xlmm_cusid):
        from flashsale.xiaolumm.models_fans import FansNumberRecord

        recod, state = FansNumberRecord.objects.get_or_create(xlmm=xlmm, xlmm_cusid=xlmm_cusid)
        if not state:
            recod.fans_num += 1
            recod.save()
        return

    def createFansRecord(self, from_customer, customer):
        """
        from_customer: 推荐人用户id
        customer: 当前用户id
        """
        from flashsale.pay.models import Customer

        current_cus = Customer.objects.filter(id=customer).exists(status=Customer.DELETE)
        from_cus = Customer.objects.filter(id=from_customer).exists(status=Customer.DELETE)

        if current_cus.exists():
            cu = current_cus[0]
            xlmm = cu.getXiaolumm()

            if xlmm:  # 如果当前用户是代理
                self.get_or_create(xlmm=xlmm.id, xlmm_cusid=cu.id)
                # 记录数量
                self.record_fans_num(xlmm.id, cu.id)
            else:  # 当前用户不是代理
                if from_cus.exists():
                    from_cu = from_cus[0]
                    from_xlmm = from_cu.getXiaolumm()

                    if from_xlmm:  # 推荐人是代理
                        self.get_or_create(xlmm=from_xlmm.id, xlmm_cusid=from_cu.id, refreal_cusid=cu.id)

                        # 记录数量
                        self.record_fans_num(from_xlmm.id, from_cu.id)

                    else:   # 推荐人也不是代理
                        fanses = self.filter(refreal_cusid=from_cu.id)  # 找到含有该推荐人的粉丝表记录
                        if fanses.exists():
                            fans = fanses[0]  # 提取记录中的　推荐人和代理创建粉丝记录
                            self.get_or_create(xlmm=fans.xlmm, xlmm_cusid=fans.xlmm_cusid,
                                               refreal_cusid=fans.refreal_cusid, fans_cusid=cu.id)

                            # 记录数量
                            self.record_fans_num(fans.xlmm, fans.fans.xlmm_cusid)
        return

