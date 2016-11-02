# -*- coding:utf-8 -*-
import random
import datetime
from django.db import models
from django.db.models import Q, Sum
from django.forms.models import model_to_dict

from core.managers import BaseManager
from shopapp.signals import weixin_referal_signal


class WeixinProductManager(BaseManager):
    def getOrCreate(self, product_id, force_update=False):

        product, state = self.get_or_create(product_id=product_id)

        if not force_update and not state and product.status:
            return product

        from .weixin_apis import WeiXinAPI

        _wx_api = WeiXinAPI()
        product_dict = _wx_api.getMerchant(product_id)

        category_list = product_dict['product_base'].get('category_id', [])
        for category_id in category_list:
            self.createSkuPropertyByCategory(category_id)

        return self.createByDict(product_dict)

    def createSkuPropertyByCategory(self, category_id):

        from .weixin_apis import WeiXinAPI
        from .models import WXSkuProperty

        _wx_api = WeiXinAPI()

        sku_tables = _wx_api.getSkuByCategory(cate_id=category_id)
        for sku_table in sku_tables:
            for sku_dict in sku_table.get('value_list', []):
                WXSkuProperty.objects.get_or_create(sku_id=sku_dict['id'], name=sku_dict['name'])

    def createByDict(self, product_dict):

        from .models import WXProductSku

        product_id = product_dict['product_id']

        product, state = self.get_or_create(product_id=product_id)

        for k, v in product_dict.iteritems():
            hasattr(product, k) and setattr(product, k, v)

        product.product_name = product.product_base.get('name', '')
        product.product_img = product.product_base.get('img', '')

        product.save()

        sku_ids = []
        for sku_dict in product.sku_list:
            self.createSkuByDict(product, sku_dict)
            sku_ids.append(sku_dict['sku_id'])

        WXProductSku.objects.filter(product=product).exclude(
            sku_id__in=sku_ids).update(status=WXProductSku.DOWN_SHELF)

        return product

    def createSkuByDict(self, product, sku_dict):

        from .models import WXProductSku
        from shopback.items.models import Product

        sku_id = sku_dict['sku_id']
        product_sku, state = WXProductSku.objects.get_or_create(product=product,
                                                                sku_id=sku_id)

        product_sku.outer_id, product_sku.outer_sku_id = Product.objects.trancecode(
            sku_dict['product_code'], '',
            sku_code_prior=True)

        product_sku.sku_name = WXProductSku.getSkuNameBySkuId(sku_id)
        product_sku.sku_img = sku_dict['icon_url']
        product_sku.sku_num = sku_dict['quantity']

        product_sku.sku_price = round(float(sku_dict['price']) / 100, 2)
        product_sku.ori_price = round(float(sku_dict['ori_price']) / 100, 2)
        product_sku.status = WXProductSku.UP_SHELF

        product_sku.save()

    def fetchSkuMatchInfo(self, product):

        from .models import WXProductSku
        product_dict = model_to_dict(product)
        product_dict['pskus'] = []

        outer_id = product.outer_id
        for sku in product.pskus.order_by('outer_id'):

            sku_dict = model_to_dict(sku)
            sku_dict['name'] = sku.name
            outer_sku_id = sku.outer_id
            wsku_dict_list = []
            wsku_list = WXProductSku.objects.filter(
                outer_id=outer_id,
                outer_sku_id=outer_sku_id,
                status=WXProductSku.UP_SHELF).order_by('-modified')
            for wsku in wsku_list:
                wsku_dict = model_to_dict(wsku)
                wsku_dict['sku_image'] = wsku.sku_image
                wsku_dict_list.append(wsku_dict)

            sku_dict['wskus'] = wsku_dict_list

            product_dict['pskus'].append(sku_dict)

        msku_ids = set([s['outer_id'] for s in product_dict['pskus']])
        product_dict['uskus'] = []
        wsku_list = WXProductSku.objects.filter(outer_id=outer_id,
                                                status=WXProductSku.UP_SHELF).order_by('-modified')
        for wsku in wsku_list:
            if wsku.outer_sku_id in msku_ids:
                continue
            wsku_dict = model_to_dict(wsku)
            wsku_dict['sku_image'] = wsku.sku_image
            product_dict['uskus'].append(wsku_dict)

        return product_dict

    @property
    def UPSHELF(self):
        return self.get_queryset().filter(status=self.model.UP_SHELF)

    @property
    def DOWNSHELF(self):
        return self.get_queryset().filter(status=self.model.DOWN_SHELF)


class WeixinUserManager(BaseManager):
    def createReferalShip(self, referal_openid, referal_from_openid):

        if referal_openid == referal_from_openid:
            return False

        wx_user = self.get(openid=referal_openid)

        if wx_user.referal_from_openid:
            return wx_user.referal_from_openid == referal_from_openid

        wx_user.referal_from_openid = referal_from_openid
        wx_user.save()

        from shopapp.weixin.models import SampleOrder

        weixin_referal_signal.send(sender=SampleOrder,
                                   user_openid=referal_openid,
                                   referal_from_openid=referal_from_openid)

        return True

    @property
    def NORMAL_USER(self):
        return self.get_queryset().exclude(user_group_id=2)

    @property
    def VALID_USER(self):
        return self.get_queryset().exclude(user_group_id=2).filter(isvalid=True)

    def charge(self, wx_user, user, *args, **kwargs):

        from .models import WXUserCharge

        try:
            WXUserCharge.objects.get(wxuser_id=wx_user.id,
                                     status=WXUserCharge.EFFECT)
        except WXUserCharge.DoesNotExist:
            WXUserCharge.objects.get_or_create(
                wxuser_id=wx_user.id,
                employee=user,
                status=WXUserCharge.EFFECT)

        else:
            return False

        wx_user.charge_status = self.model.CHARGED
        wx_user.save()
        return True

    def uncharge(self, wx_user, *args, **kwargs):

        from .models import WXUserCharge

        try:
            scharge = WXUserCharge.objects.get(
                wxuser_id=wx_user.id,
                status=WXUserCharge.EFFECT)
        except WXUserCharge.DoesNotExist:
            return False
        else:
            scharge.status = WXUserCharge.INVALID
            scharge.save()

        wx_user.charge_status = self.model.UNCHARGE
        wx_user.save()
        return True


NUM_CHAR_LIST = list('1234567890')


class VipCodeManager(BaseManager):
    def genCode(self):
        return ''.join(random.sample(NUM_CHAR_LIST, 7))

    def genVipCodeByWXUser(self, wx_user):

        vipcodes = self.filter(owner_openid=wx_user)
        if vipcodes.count() > 0:
            return vipcodes[0].code

        expiry = datetime.datetime(2014, 9, 7, 0, 0, 0)
        code_type = 0
        code_rule = u'免费试用'
        max_usage = 10000

        new_code = self.genCode()
        cnt = 0
        while True:
            cnt += 1
            try:
                vipcode = self.get(owner_openid=wx_user)
            except self.model.DoesNotExist:
                try:
                    self.create(owner_openid=wx_user, code=new_code, expiry=expiry,
                                code_type=code_type, code_rule=code_rule, max_usage=max_usage)
                except:
                    new_code = self.genCode()
                else:
                    return new_code
            else:
                return vipcode.code

            if cnt > 20:
                raise Exception(u'F码生成异常')
