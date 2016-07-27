# coding:utf-8
from django.db import transaction
from django.shortcuts import redirect
from django.core.urlresolvers import reverse

from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import exceptions
from rest_framework import authentication
from rest_framework.decorators import detail_route, list_route

from flashsale.pay.models import ModelProduct, Productdetail, default_modelproduct_extras_tpl
from flashsale.pay.signals import signal_record_supplier_models
from flashsale.xiaolumm.models_rebeta import AgencyOrderRebetaScheme
from shopback.categorys.models import ProductCategory
from shopback.items.models import (Product, ProductSku, ProductSchedule,
                                   ProductSkuContrast, ContrastContent, ProductSkuStats)
from core.options import log_action, ADDITION, CHANGE
from supplychain.supplier.models import SaleSupplier, SaleProduct, SaleCategory

from shopback.items import constants, forms, local_cache
from flashsale.pay.models import ModelProduct

import logging
logger = logging.getLogger(__name__)

class ProductManageViewSet(viewsets.ModelViewSet):

    queryset = ModelProduct.objects.all()
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    authentication_classes = (authentication.BasicAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        supplier_id = request.GET.get('supplier_id')
        saleproduct_id = request.GET.get('saleproduct')
        saleproduct = SaleProduct.objects.filter(id=saleproduct_id).first()
        firstgrade_cat =saleproduct and saleproduct.sale_category.get_firstgrade_category()
        if firstgrade_cat and (str(firstgrade_cat.cid)).startswith(constants.CATEGORY_HEALTH):
            return redirect(reverse('items_v1:modelproduct-health')+'?supplier_id=%s&saleproduct=%s'%(supplier_id, saleproduct_id))
        elif firstgrade_cat and str(firstgrade_cat.cid).startswith((constants.CATEGORY_CHILDREN,
                                                constants.CATEGORY_WEMON ,
                                                constants.CATEGORY_ACCESSORY)):
            return redirect('/static/add_item.html?supplier_id=%s&saleproduct=%s'%(supplier_id, saleproduct_id))
        return Response({
                "supplier": SaleSupplier.objects.filter(id=supplier_id).first(),
                "saleproduct": SaleProduct.objects.filter(id=saleproduct_id).first()
            }, template_name='items/add_item.html')

    @list_route(methods=['get'])
    def health(self, request, *args, **kwargs):
        data = request.GET
        supplier_id = data.get('supplier_id') or 0
        saleproduct_id = data.get('saleproduct') or 0

        return Response({
                "supplier": SaleSupplier.objects.filter(id=supplier_id).first(),
                "saleproduct": SaleProduct.objects.filter(id=saleproduct_id).first()
            },
            template_name='items/add_item_health.html'
        )

    @list_route(methods=['post'])
    def multi_create(self, request, *args, **kwargs):
        """ 新增库存商品　新增款式
        {
          "qs_code": "",
          "products": [
            {
              "remain_num": "1",
              "agent_price": "4",
              "cost": "2",
              "name": "\u82e6\u4e01\u8336",
              "std_sale_price": "3"
            },
            {
              "remain_num": "1",
              "agent_price": "4",
              "cost": "2",
              "name": "\u5c71\u6942\u5e72",
              "std_sale_price": "3"
            },
            {
              "remain_num": "1",
              "agent_price": "4",
              "cost": "2",
              "name": "\u8377\u53f6\u8336",
              "std_sale_price": "3"
            }
          ],
          "name": "",
          "sale_time": "",
          "category_id": "19",
          "memo": "",
          "head_img": "",
          "saleproduct_id": "",
          "qhby_code": ""
        }
        """
        content = request.data
        creator = request.user
        saleproduct_id = content.get("saleproduct_id", "")
        saleproduct = SaleProduct.objects.filter(id=saleproduct_id).first()
        if not saleproduct:
            return exceptions.APIException(u"选品ID错误")

        supplier = saleproduct.sale_supplier
        category_id = content.get("category_id", "")
        category_item = ProductCategory.objects.get(cid=category_id)
        if category_item.parent_cid == 3:
            first_outer_id = u"3"
            outer_id = first_outer_id + str(category_item.cid) + "%05d" % supplier.id
        elif category_item.parent_cid == 5:
            first_outer_id = u"9"
            outer_id = first_outer_id + str(category_item.cid) + "%05d" % supplier.id
        elif category_item.parent_cid == 8:
            first_outer_id = u"8"
            outer_id = first_outer_id + str(category_item.cid) + "%05d" % supplier.id
        elif category_item.cid == 9:
            outer_id = "100" + "%05d" % supplier.id
        else:
            return exceptions.APIException(u"类别错误")

        count = Product.objects.filter(outer_id__startswith=outer_id).count() or 1
        while True:
            inner_outer_id = outer_id + "%03d" % count
            product_ins = Product.objects.filter(outer_id__startswith=inner_outer_id).count()
            if not product_ins or count > 998:
                break
            count += 1
        if len(inner_outer_id) > 12:
            return exceptions.APIException(u"编码生成错误")
        try:
            extras = default_modelproduct_extras_tpl()
            extras['properties'].update({
                'qs_code': content['qs_code'],
                'qhby_code': content['qhby_code']
            })
            with transaction.atomic():
                model_pro = ModelProduct(
                    name=content['name'],
                    head_imgs=content['head_img'],
                    sale_time=content['sale_time'],
                    salecategory=saleproduct.sale_category,
                    is_flatten=True,
                    extras=extras,
                )
                model_pro.save()
                log_action(creator.id, model_pro, ADDITION, u'新建一个modelproduct new')
                pro_count = 1
                for color in content['products']:
                    # product除第一个颜色外, 其余的颜色的outer_id末尾不能为1
                    if (pro_count % 10) == 1 and pro_count > 1:
                        pro_count += 1

                    one_product = Product(
                        name=content['name'] + "/" + color['name'],
                        outer_id=inner_outer_id + str(pro_count),
                        model_id=model_pro.id,
                        sale_charger=creator.username,
                        category=category_item,
                        remain_num=color['remain_num'],
                        cost=color['cost'],
                        agent_price=color['agent_price'],
                        std_sale_price=color['std_sale_price'],
                        ware_by=supplier.ware_by,
                        sale_time=content['sale_time'],
                        pic_path=content['head_img'],
                        sale_product=saleproduct.id,
                        is_flatten=True,
                    )
                    one_product.save()
                    log_action(creator.id, one_product, ADDITION, u'新建一个product_new')
                    pro_count += 1
                    # one_product_detail = Productdetail(
                    #     product=one_product, material=material,
                    #     color=content.get("all_colors", ""),
                    #     wash_instructions=wash_instroduce, note=note
                    # )
                    # one_product_detail.save()

                    barcode = '%s%d'%(one_product.outer_id ,1)
                    one_sku = ProductSku(outer_id=barcode, product=one_product,
                                         remain_num=color['remain_num'], cost=color['cost'],
                                         std_sale_price=color['std_sale_price'], agent_price=color['agent_price'],
                                         properties_name=color['name'], properties_alias=color['name'],
                                         barcode=barcode)
                    one_sku.save()
                    try:
                        ProductSkuStats.get_by_sku(one_sku.id)
                    except Exception, exc:
                        logger.error('product skustats:new_sku_id=%s, %s' % (one_sku.id, exc.message), exc_info=True)

        except Exception, exc:
            logger.error(exc.message or u'商品资料创建错误', exc_info=True)
            raise exceptions.APIException(u'出错了:%s' % exc.message)
        # 发送　添加供应商总选款的字段　的信号
        try:
            signal_record_supplier_models.send(sender=ModelProduct, obj=model_pro)
        except Exception, exc:
            logger.error(exc.message or u'创建商品model异常', exc_info=True)
            raise exceptions.APIException(u'创建商品model异常:%s' % exc.message)

        return Response({'code': 0 ,'info': u'创建成功'})