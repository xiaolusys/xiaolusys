# coding:utf-8
import logging
from collections import OrderedDict

from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import list_route, detail_route
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework import filters

from core.options import log_action, ADDITION, CHANGE
from flashsale.pay.models import ModelProduct, Productdetail
from flashsale.pay.models import default_modelproduct_extras_tpl
from flashsale.pay.signals import signal_record_supplier_models
from shopback.categorys.models import ProductCategory
from shopback.items import constants
from shopback.items.models import (Product, ProductSku, ProductSkuStats)
from supplychain.supplier.models import SaleSupplier, SaleProduct, SaleCategory, SaleProductManageDetail
from shopback.items import serializers

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
        firstgrade_cat = saleproduct and saleproduct.sale_category.get_firstgrade_category()
        # if firstgrade_cat and (str(firstgrade_cat.cid)).startswith(constants.CATEGORY_HEALTH):
        # return redirect(reverse('items_v1:modelproduct-health') + '?supplier_id=%s&saleproduct=%s' %(supplier_id, saleproduct_id))
        # elif saleproduct.sale_category and saleproduct.sale_category.cid.startswith(constants.CATEGORY_TRUNK):
        #     return redirect(reverse('items_v1:modelproduct-cloth') + '?supplier_id=%s&saleproduct=%s' %(supplier_id, saleproduct_id))
        # elif firstgrade_cat and (str(firstgrade_cat.cid)).startswith((constants.CATEGORY_BAGS, constants.CATEGORY_MEIZUANG)):
        #     return redirect(reverse('items_v1:modelproduct-bags') + '?supplier_id=%s&saleproduct=%s' %(supplier_id, saleproduct_id))
        # elif firstgrade_cat \
        #     and not saleproduct.sale_category.cid.startswith(constants.CATEGORY_SHOES)\
        #     and (str(firstgrade_cat.cid)).startswith(constants.CATEGORY_MUYING):
        #     return redirect(reverse('items_v1:modelproduct-muying') + '?supplier_id=%s&saleproduct=%s' % (
        #         supplier_id, saleproduct_id))
        # elif firstgrade_cat \
        #     and not saleproduct.sale_category.cid.startswith(constants.CATEGORY_ACCESSOR) \
        #     and str(firstgrade_cat.cid).startswith((constants.CATEGORY_CHILDREN,
        #                                             constants.CATEGORY_WEMON)):
        #     return redirect(reverse('items_v1:modelproduct-cloth') + '?supplier_id=%s&saleproduct=%s' % (
        #         supplier_id, saleproduct_id))
        return Response({
            "supplier": SaleSupplier.objects.filter(id=supplier_id).first(),
            "saleproduct": SaleProduct.objects.filter(id=saleproduct_id).first()
        }, template_name='items/add_item.html')

    @list_route(methods=['get'])
    def cloth(self, request, *args, **kwargs):
        data = request.GET
        supplier_id = data.get('supplier_id') or 0
        saleproduct_id = data.get('saleproduct') or 0

        return Response({
            "supplier": SaleSupplier.objects.filter(id=supplier_id).first(),
            "saleproduct": SaleProduct.objects.filter(id=saleproduct_id).first()
        },
            template_name='items/add_item_cloth.html'
        )

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

    @list_route(methods=['get'])
    def bags(self, request, *args, **kwargs):
        data = request.GET
        supplier_id = data.get('supplier_id') or 0
        saleproduct_id = data.get('saleproduct') or 0

        return Response({
            "supplier": SaleSupplier.objects.filter(id=supplier_id).first(),
            "saleproduct": SaleProduct.objects.filter(id=saleproduct_id).first()
        },
            template_name='items/add_item_bags.html'
        )

    @list_route(methods=['get'])
    def muying(self, request, *args, **kwargs):
        data = request.GET
        supplier_id = data.get('supplier_id') or 0
        saleproduct_id = data.get('saleproduct') or 0

        return Response({
            "supplier": SaleSupplier.objects.filter(id=supplier_id).first(),
            "saleproduct": SaleProduct.objects.filter(id=saleproduct_id).first()
        },
            template_name='items/add_item_muying.html'
        )

    @list_route(methods=['get'])
    def homehold(self, request, *args, **kwargs):
        data = request.GET
        supplier_id = data.get('supplier_id') or 0
        saleproduct_id = data.get('saleproduct') or 0

        return Response({
            "supplier": SaleSupplier.objects.filter(id=supplier_id).first(),
            "saleproduct": SaleProduct.objects.filter(id=saleproduct_id).first()
        },
            template_name='items/add_item_homehold.html'
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
        products_data = content.get('products')
        saleproduct = SaleProduct.objects.filter(id=saleproduct_id).first()
        if not saleproduct:
            raise exceptions.APIException(u"选品ID错误")

        supplier = saleproduct.sale_supplier
        category_id = content.get("category_id", "")
        category_item = ProductCategory.objects.get(cid=category_id)
        category_maps = {
            3: '3',
            39: '3',
            6: '6',
            5: '9',
            52: '5',
            44: '7',
            8: '8',
            49: '4',
            10: '1'
        }
        if category_maps.has_key(category_item.parent_cid):
            outer_id = category_maps.get(category_item.parent_cid) + str(category_item.cid) + "%05d" % supplier.id
        elif category_item.cid == 9:
            outer_id = "100" + "%05d" % supplier.id
        else:
            raise exceptions.APIException(u"请选择正确分类")
        saleways = content.get("saleways")
        teambuy = False
        if saleways and (2 in saleways or '2' in saleways):
            teambuy = True
            teambuy_price = int(content.get("teambuy_price"))
        count = Product.objects.filter(outer_id__startswith=outer_id).count() or 1
        inner_outer_id = outer_id + "%03d" % count
        while True:
            product_ins = Product.objects.filter(outer_id__startswith=inner_outer_id).count()
            if not product_ins or count > 998:
                break
            count += 1
            inner_outer_id = outer_id + "%03d" % count

        if len(inner_outer_id) > 12:
            raise exceptions.APIException(u"编码位数不能超出12位")
        try:
            extras = default_modelproduct_extras_tpl()
            extras.setdefault('properties', {})
            for key, value in content.iteritems():
                if key.startswith('property.'):
                    name = key.replace('property.', '')
                    extras['properties'].update({name: value})
            is_flatten = False
            if len(products_data) == 1:
                skus_data = products_data[0].get('skus', [])
                if not skus_data or len(skus_data) == 1:
                    is_flatten = True

            # TODO@meron 考虑到亲子装问题，支持同一saleproduct录入多个modelproduct
            with transaction.atomic():
                model_pro = ModelProduct(
                    name=content['name'],
                    head_imgs=content['head_img'],
                    salecategory=saleproduct.sale_category,
                    saleproduct=saleproduct,
                    is_flatten=is_flatten,
                    lowest_agent_price=round(min([float(p['agent_price']) for p in products_data]), 2),
                    lowest_std_sale_price=round(min([float(p['std_sale_price']) for p in products_data]), 2),
                    extras=extras,
                )
                if teambuy:
                    model_pro.is_teambuy = True
                    model_pro.teambuy_price = teambuy_price
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
                        pic_path=content['head_img'],
                        sale_product=saleproduct.id,
                        is_flatten=is_flatten,
                    )
                    one_product.save()
                    log_action(creator.id, one_product, ADDITION, u'新建一个product_new')
                    pro_count += 1
                    # one_product_detail = Productdetail(
                    # product=one_product, material=material,
                    # color=content.get("all_colors", ""),
                    # wash_instructions=wash_instroduce, note=note
                    # )
                    # one_product_detail.save()

                    barcode = '%s%d' % (one_product.outer_id, 1)
                    one_sku = ProductSku(outer_id=barcode, product=one_product,
                                         remain_num=color['remain_num'], cost=color['cost'],
                                         std_sale_price=color['std_sale_price'], agent_price=color['agent_price'],
                                         properties_name=color['name'], properties_alias=color['name'],
                                         barcode=barcode)
                    one_sku.save()
                    try:
                        ProductSkuStats.get_by_sku(one_sku.id)
                    except Exception, exc:
                        logger.error('product skustats:　new_sku_id=%s, %s' % (one_sku.id, exc.message), exc_info=True)

        except Exception, exc:
            logger.error('%s' % exc or u'商品资料创建错误', exc_info=True)
            raise exceptions.APIException(u'出错了:%s' % exc)
        # 发送　添加供应商总选款的字段　的信号
        try:
            signal_record_supplier_models.send(sender=ModelProduct, obj=model_pro)
        except Exception, exc:
            logger.error('%s' % exc or u'创建商品model异常', exc_info=True)
            raise exceptions.APIException(u'创建商品model异常:%s' % exc)

        SaleProductManageDetail.objects.set_material_complete_by_saleproduct(saleproduct)

        logger.info('modelproduct-create: inner_outer_id= %s, model_id= %s' % (inner_outer_id, model_pro.id))
        return Response({'code': 0, 'info': u'创建成功', 'modelproduct_id': model_pro.id})


class ModelProductFilter(filters.FilterSet):
    class Meta:
        model = ModelProduct
        fields = ['id', 'status', 'saleproduct', 'shelf_status', 'is_onsale', 'is_teambuy']


class ProductManageV2ViewSet(viewsets.ModelViewSet):
    """
    ### 款式及产品接口
    - [/apis/items/v2/product](/apis/items/v2/product)
        * method: POST  新增款式
        * args:
            1. `saleproduct_id`: 选品id
            2. `is_onsale: 是否秒杀
            3. `is_teambuy` : 是否团购 例如： true
            4. `teambuy_price` : 团购价格  例如： 23.3
            5. `teambuy_person_num` : 团购人数 默认为3
            6. `status` : 使用状态 (正常: "normal" /作废: "delete")
            7. `is_recommend` : 是否是推荐商品
            7. `new_properties`:"new_properties": [
                                                    {
                                                        "name": "材质",
                                                        "value": "牛皮"
                                                    },
                                                    {
                                                        "name": "产品备注",
                                                        "value": "10岁以上穿着"
                                                    },
                                                    {
                                                        "name": "可选颜色",
                                                        "value": "黑色,绿色,红色,蓝色"
                                                    },
                                                    {
                                                        "name": "洗涤说明",
                                                        "value": "温水擦拭"
                                                    },
                                                    {
                                                        "name": "尺码表",
                                                        "value": [
                                                            {
                                                                "尺码": "L",
                                                                "衣长": "35",
                                                                "肩宽": "36",
                                                                "胸围": "37",
                                                                "袖长": "38",
                                                                "建议体重": "39",
                                                                "建议身高": "40"
                                                            },
                                                            {
                                                                "尺码": "M",
                                                                "衣长": "41",
                                                                "肩宽": "42",
                                                                "胸围": "43",
                                                                "袖长": "44",
                                                                "建议体重": "45",
                                                                "建议身高": "46"
                                                            }
                                                        ]
                                                    },
                                                    {
                                                        "name": "尺码对照参数",
                                                        "value": [
                                                           "尺码",
                                                            "衣长",
                                                            "肩宽",
                                                            "胸围",
                                                            "袖长",
                                                            "建议体重",
                                                            "建议身高"
                                                        ]
                                                    }
                                                ]
    -------
    - [/apis/items/v2/product/update_product_details]()
        * method: PATCH  修改指定款式id的款式
        * args:　同 POST 方法
    """
    queryset = ModelProduct.objects.all()
    serializer_class = serializers.ModelProductSerializer
    authentication_classes = (authentication.BasicAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser, permissions.DjangoModelPermissions)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_class = ModelProductFilter
    ordering_fields = ('created', 'id', 'order_weight', 'lowest_agent_price', 'lowest_std_sale_price')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        raise exceptions.APIException(u'Method Not Allowed!')

    def get_request_properties(self, request, model_product=None):
        content = request.data
        extras = default_modelproduct_extras_tpl()  # 可选颜色 材质 备注 洗涤说明
        if model_product:
            extras = model_product.extras
        properties = extras.get('new_properties')
        model_properties = content.get('new_properties') or None
        print 'new_properties', model_properties
        if isinstance(model_properties, list):
            model_properties_d = dict([(tt['name'], tt['value']) for tt in model_properties])
            old_properties_d = dict(
                [(tt['name'], tt['value']) for tt in properties]) if properties else model_properties_d
            old_properties_d.update(model_properties_d)
            properties = [{'name': k, "value": v} for k, v in old_properties_d.iteritems()]

        properties_copy = []
        thead = []
        tbody = []
        for propto in properties:
            if propto['name'] == '尺码对照参数':
                thead = propto['value']
            elif propto['name'] == '尺码表':
                tbody = propto['value']
            else:
                properties_copy.append(propto)
        return  properties_copy


    def get_request_extras(self, request, model_product=None):
        """ 更新款式额外属性 """
        content = request.data
        extras = default_modelproduct_extras_tpl()  # 可选颜色 材质 备注 洗涤说明
        if model_product:
            extras = model_product.extras
        extras.setdefault('new_properties', [])
        properties = extras.get('new_properties')
        model_properties = content.get('new_properties') or None

        if isinstance(model_properties, list):
            model_properties_d = dict([(tt['name'], tt['value']) for tt in model_properties])
            old_properties_d = dict(
                [(tt['name'], tt['value']) for tt in properties]) if properties else model_properties_d
            old_properties_d.update(model_properties_d)
            properties = [{'name': k, "value": v} for k, v in old_properties_d.iteritems()]

        properties_copy = []
        thead = []
        tbody = []
        for propto in properties:
            if propto['name'] == '尺码对照参数':
                thead = propto['value']
            elif propto['name'] == '尺码表':
                tbody = propto['value']
            else:
                properties_copy.append(propto)

        values = [thead]
        for body in tbody:
            line = []
            for x in thead:
                line.append(body[x])
            values.append(line)
        extras.update({'tables': [{'table': values}]})
        extras.update({'new_properties': properties_copy})
        return extras

    def set_model_pro(self, model_pro):
        model_pro.set_is_flatten()  # 设置平铺字段
        model_pro.set_lowest_price()  # 设置款式最低价格
        return

    @transaction.atomic()
    def create(self, request, *args, **kwargs):
        """ 创建特卖款式 """
        content = request.data
        saleproduct_id = content.get("saleproduct_id") or 0
        saleproduct = SaleProduct.objects.filter(id=saleproduct_id).first()
        if not saleproduct:
            raise exceptions.APIException(u"选品ID错误!")
        if ModelProduct.objects.filter(saleproduct=saleproduct, status=ModelProduct.NORMAL).exists():
            raise exceptions.APIException(u'该商品款式已存在!')
        extras = self.get_request_extras(request)
        request.data.update({'name': saleproduct.title})
        request.data.update({'head_imgs': saleproduct.pic_url})

        request.data.update({'extras': extras})
        request.data.update({'saleproduct': saleproduct.id})
        request.data.update({'salecategory': saleproduct.sale_category.id})

        serializer = serializers.ModelProductUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        model_pro = get_object_or_404(ModelProduct, id=serializer.data.get('id'))
        log_action(request.user.id, model_pro, ADDITION, u'新建特卖款式')
        # 生成sku信息
        creator = request.user
        Product.create_or_update_skus(model_pro, creator)

        SaleProductManageDetail.objects.set_material_complete_by_saleproduct(saleproduct)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @list_route(methods=['patch'])
    def update_product_details(self, request, *args, **kwargs):
        content = request.data
        saleproduct_id = content.get("saleproduct_id") or 0
        saleproduct = SaleProduct.objects.filter(id=saleproduct_id).first()
        if not saleproduct:
            raise exceptions.APIException(u"选品ID错误!")
        content_imgs = content.get('content_imgs') or ''
        if isinstance(content_imgs, list):
            request.data.update({'content_imgs': '\n'.join(content_imgs)})
        instance = saleproduct.model_product
        partial = kwargs.pop('partial', False)
        new_properties = request.data.get('new_properties') or None
        request_extras = request.data.get('extras') or None
        if request_extras is not None or new_properties :
            extras = self.get_request_extras(request, instance)
            request.data.update({'extras': extras})

        request.data.update({'name': saleproduct.title})
        request.data.update({'salecategory': instance.salecategory.id})  # 类别不予更新（使用原来的类别）
        request.data.update({'lowest_agent_price': instance.lowest_agent_price})  # 最低售价（价格由sku决定）
        request.data.update({'lowest_std_sale_price': instance.lowest_std_sale_price})  # 最低吊牌价（价格由sku决定）
        serializer = serializers.ModelProductUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        log_action(request.user, instance, CHANGE, u'修改款式信息')
        return Response(serializer.data)
