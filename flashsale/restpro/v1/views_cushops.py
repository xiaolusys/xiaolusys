# coding=utf-8
import datetime
import random
import urllib
import urlparse
from django.db.models import F
from django.conf import settings
from django.forms import model_to_dict
from django.shortcuts import get_object_or_404

from rest_framework import exceptions
from rest_framework import viewsets, permissions, authentication
from rest_framework.decorators import list_route
from rest_framework.response import Response

from shopback.items.models import Product
from flashsale.restpro.utils import save_pro_info
from flashsale.xiaolumm.models.models_rebeta import AgencyOrderRebetaScheme
from flashsale.xiaolumm.models import XiaoluMama, MamaTabVisitStats
from flashsale.pay.models import Customer, CustomerShops, CuShopPros
from flashsale.restpro import permissions as perms
from common.urlutils import replace_domain
from . import serializers


class CustomerShopsViewSet(viewsets.ModelViewSet):
    """
    ### 特卖用户店铺接口
    - {prefix} 获取用户店铺的信息
    """
    queryset = CustomerShops.objects.all()
    serializer_class = serializers.CustomerShopsSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_shop(request))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        exceptions.APIException(u'方法不允许')

    def get_owner_shop(self, request):
        """ 用户个人店铺信息 """
        customer = get_object_or_404(Customer, user=request.user)
        shops = self.queryset.filter(customer=customer.id)  # 获取店铺
        if not shops.exists():  # 创建店铺
            CustomerShops.create_shop(customer)
        shops = self.queryset.filter(customer=customer.id)  # 获取店铺
        return shops

    @list_route(methods=['get'])
    def customer_shop(self, request):
        decs = ['今天又上新品啦！', '天天都有新品哦！', '上新品啦赶快抢！']
        queryset = self.filter_queryset(self.get_owner_shop(request))
        mm_linkid = 44
        shop_info = None
        if queryset.exists():
            shop = queryset[0]
            customer = shop.get_customer()
            if customer:
                xlmm = customer.get_charged_mama()
                if xlmm:
                    mm_linkid = xlmm.id
                    from flashsale.xiaolumm.tasks import task_mama_daily_tab_visit_stats
                    task_mama_daily_tab_visit_stats.delay(xlmm.id, MamaTabVisitStats.TAB_MAMA_SHOP)
                    
            shop_info = model_to_dict(shop)

            link = '/mall/?mm_linkid={0}'.format(mm_linkid)
            preview_link = 'mall/?mm_linkid={0}'.format(mm_linkid)

            link = urllib.quote(link)
            next_link = 'm/{0}?next='.format(mm_linkid) + link
            link = urlparse.urljoin(settings.M_SITE_URL, next_link)

            preview_link = urlparse.urljoin('http://m.xiaolumeimei.com', preview_link)
            first_pro_pic = customer.thumbnail
            shop_info['shop_link'] = replace_domain(link)
            shop_info['thumbnail'] = first_pro_pic  # customer.thumbnail  # 提供用户头像
            shop_info['desc'] = '{0}の精品店铺'.format(customer.nick) + random.choice(decs)
            shop_info['preview_shop_link'] = preview_link  # 预览链接http
            shop_info['name'] = '{0}の精品店铺'.format(customer.nick)
            shop_info['first_pro_pic'] = first_pro_pic

        return Response({"shop_info": shop_info})


class CuShopProsViewSet(viewsets.ModelViewSet):
    """
    ### 特卖用户店铺产品接口  
    - {prefix} 获取用户店铺产品的信息  
        `id`: 产品id  
        `status`: 店铺产品状态　1　表示上架　0 表示没有上架  
        `name`: 产品名称  
    - {prefix}/add_pro_to_shop [method:post] 添加商品到店铺  
        `product`: 要添加的产品id  
        :return 0 添加成功  
                1 参数缺失  
                2 添加错误  
    - {prefix}/remove_pro_from_shop [method:post] 下架我的店铺商品  
        `product`: 要下架的产品id  
        :return 0 下架成功  
                1 参数缺失  
    """
    queryset = CuShopPros.objects.all()
    child_queryset = CuShopPros.objects.child_query()
    female_queryset = CuShopPros.objects.female_query()
    serializer_class = serializers.CuShopProsSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_shop_pros(self, request):
        """ 用户个人店铺产品信息 """
        customer = get_object_or_404(Customer, user=request.user)
        shop_pros = self.queryset.filter(customer=customer.id).order_by("-position")
        return shop_pros

    def get_owner_child_pros(self, request):
        """ 用户个人店铺产品信息 """
        customer = get_object_or_404(Customer, user=request.user)
        shop_pros = self.child_queryset.filter(customer=customer.id)
        return shop_pros

    def get_owner_female_pros(self, request):
        """ 用户个人店铺产品信息 """
        customer = get_object_or_404(Customer, user=request.user)
        shop_pros = self.female_queryset.filter(customer=customer.id)
        return shop_pros

    def get_owner_up_pros(self, request):
        """ 获取用户上架商品"""
        return self.get_owner_shop_pros(request).filter(pro_status=CuShopPros.UP_SHELF)

    def get_owner_child_up_pros(self, request):
        """ 获取用户上架商品"""
        return self.get_owner_child_pros(request).filter(pro_status=CuShopPros.UP_SHELF)

    def get_owner_female_up_pros(self, request):
        """ 获取用户上架商品"""
        return self.get_owner_female_pros(request).filter(pro_status=CuShopPros.UP_SHELF)

    def list(self, request, *args, **kwargs):
        shop_pros = self.get_owner_up_pros(request)
        data = []
        customer = get_object_or_404(Customer, user=request.user)
        try:
            xlmm = XiaoluMama.objects.get(openid=customer.unionid)
        except XiaoluMama.DoesNotExist:
            raise exceptions.APIException(u'请先申请成为小鹿妈妈')
        for shop_pro in shop_pros:
            pro = Product.objects.get(id=shop_pro.product)  # 产品信息
            if pro.status == Product.NORMAL and pro.shelf_status == Product.UP_SHELF:  # 正常使用状态和上架状态的产品
                pro_dic = model_to_dict(pro, fields=['id', 'pic_path', 'name', 'std_sale_price', 'agent_price',
                                                     'remain_num'])
                # 修改销量为0　bug 预留数量
                sale_num = pro_dic['remain_num'] * 19 + random.choice(xrange(19))
                pro_dic['sale_num'] = sale_num
                pro_dic['product'] = pro_dic['id']

                rebeta_scheme_id = pro.detail and pro.detail.rebeta_scheme_id or 0
                rebate = AgencyOrderRebetaScheme.get_rebeta_scheme(rebeta_scheme_id)
                rebet_amount = rebate.calculate_carry(xlmm.agencylevel, float(pro.agent_price))  # 计算佣金

                pro_dic['status'] = shop_pro.pro_status
                pro_dic['rebet_amount'] = rebet_amount
                data.append(pro_dic)
            else:
                # 保存为下架（如果重新上架需要用户从选品上架点击加入店铺才会修改该状态为上架状态）
                shop_pro.pro_status = CuShopPros.DOWN_SHELF
                shop_pro.save()
        return Response(data)

    @list_route(methods=['get'])
    def shop_product(self, request):
        """ 用户商店产品信息 """
        shop_pros = self.get_owner_up_pros(request)
        page = self.paginate_queryset(shop_pros)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(page, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def shop_child_product(self, request):
        """ 用户商店童装产品信息 """
        shop_pros = self.get_owner_child_up_pros(request)
        page = self.paginate_queryset(shop_pros)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(page, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def shop_female_product(self, request):
        """ 用户商店女装产品信息 """
        shop_pros = self.get_owner_female_up_pros(request)
        page = self.paginate_queryset(shop_pros)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(page, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('method no allowed')

    @list_route(methods=['post'])
    def add_pro_to_shop(self, request, *args, **kwargs):
        content = request.data
        product = content.get('product', None)
        if product is None:
            return Response({"code": 1, 'message': '缺少参数'})  # 参数缺失
        user = request.user
        shop_pro, pro_state = save_pro_info(product, user)
        if not shop_pro:
            return Response({"code": 2, "message": "商品信息出错"})
        if pro_state:  # 新建成功
            position = self.get_owner_shop_pros(request).count()
            shop_pro.position = position + 1
            shop_pro.save()
            return Response({"code": 0, "message": "添加成功"})
        shop_pro.up_shelf_pro()  # 如果不是创建的修改为上架状态
        return Response({"code": 0, "message": "已经添加"})

    @list_route(methods=['post'])
    def remove_pro_from_shop(self, request):
        content = request.data
        product = content.get('product', None)
        if product is None:
            return Response({"code": 1})  # 参数缺失
        down_pro = self.get_owner_shop_pros(request).filter(product=product, pro_status=CuShopPros.UP_SHELF)
        down_pro.update(pro_status=CuShopPros.DOWN_SHELF)  # 更新我的店铺产品状态到下架
        return Response({"code": 0})

    @list_route(methods=['post'])
    def change_pro_position(self, request):
        """
        更换商品位置
        参数：需要换的产品 change_pro　更换到哪个位置的产品 target_pro
        注意：默认是放到目标位置的上面, position 排序
        """
        content = request.data
        change_id = content.get("change_id", None)
        target_id = content.get("target_id", None)
        target_position, change_position = 0, 0
        if not (change_id and target_id):
            return Response({"code": 1, "message": "参数缺失"})
        change_pros = self.get_owner_up_pros(request).filter(id=change_id)
        if change_pros.exists():
            change_pro = change_pros[0]
            change_position = change_pro.position

        target_pros = self.get_owner_up_pros(request).filter(id=target_id)
        if target_pros:
            target_pro = target_pros[0]
            target_position = target_pro.position

        if not (target_position and change_position):
            return Response({"code": 2, "message": "参数缺失"})

        if change_position > target_position:  # 表示从上面向下拉
            # 两个产品之间的产品的位置号都加１
            pros = self.get_owner_up_pros(request).filter(position__gt=target_position, position__lt=change_position)
            for pro in pros:
                pro.position = F('position') + 1
                pro.save()
            change_pros = self.get_owner_up_pros(request).filter(id=change_id)
            if change_pros.exists():
                change_pro = change_pros[0]
                change_pro.position = target_position + 1
                change_pro.save()

        elif change_position < target_position:  # 表示从下面向上拉
            pros = self.get_owner_up_pros(request).filter(position__gt=change_position, position__lte=target_position)
            for pro in pros:
                pro.position = F('position') - 1
                pro.save()
            change_pros = self.get_owner_up_pros(request).filter(id=change_id)
            if change_pros.exists():
                ch_pro = change_pros[0]
                ch_pro.position = target_position
                ch_pro.save()
        return Response({"code": 0, "message": "更换成功"})

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('method not allowed')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('method not allowed')

    def perform_update(self, serializer):
        raise exceptions.APIException('method not allowed')
