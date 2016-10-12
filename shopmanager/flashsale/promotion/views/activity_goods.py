# coding=utf-8
import re
from collections import defaultdict

from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response

from flashsale.promotion.models import ActivityProduct, ActivityEntry
from flashsale.promotion.serializers import ActivityProductSerializer
from apis.v1.products import ModelProductCtl

class ActivityGoodsViewSet(viewsets.ModelViewSet):
    queryset = ActivityProduct.objects.all()
    serializer_class = ActivityProductSerializer
    # authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    # permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    @list_route(methods=['get'])
    def get_goods_pics_by_promotionid(self, request, **kwargs):
        content = request.REQUEST
        promotion_id = content.get('promotion_id', None)
        brand_entry = ActivityEntry.objects.filter(id=promotion_id).first()

        if brand_entry:
            act_pics = brand_entry.activity_products.order_by("location_id")
            serializer = self.get_serializer(act_pics, many=True)
            return Response(serializer.data)
        else:
            return Response([])

    # @list_route(methods=['get'])
    # def get_desc_pics_by_promotionid(self, request):
    #     content = request.REQUEST
    #     promotion_id = content.get('promotion_id', None)
    #     desc_pics = ActivityEntry.objects.filter(id=promotion_id)
    #     if desc_pics:
    #         return Response(desc_pics.first().extra_pic)
    #     else:
    #         return Response([])

    @list_route(methods=['post'])
    def save_pics(self, request, **kwargs):

        content = request.REQUEST
        arr = content.get("arr", None)
        act_id = content.get("promotion_id", None)
        data = eval(arr)  # json字符串转化

        activity = ActivityEntry.objects.filter(id=act_id).first()
        # ActivityProduct.objects.filter(brand=brand).delete()
        if activity:
            activity.activity_products.all().delete()
            activity.extras = {}
            activity.save()
        else:
            return Response({"code": 1, "info": "需要先建立这些商品的推广专题-Pay › 特卖/推广专题入口 "})

        for da in data:
            try:
                pic_type = int(da['pic_type'])
            except ValueError:
                pic_type = 0

            try:
                model_id = int(da['model_id'])
            except ValueError:
                model_id = 0

            product_name = da['product_name']
            pic_path = da['pic_path']

            try:
                location_id = int(da['location_id'])
            except ValueError:
                location_id = 0

            jump_url = da['jump_url']
            pics = ActivityProduct.objects.create(activity=activity,
                                                  model_id=model_id,
                                                  product_name=product_name,
                                                  product_img=pic_path,
                                                  location_id=location_id,
                                                  pic_type=pic_type,
                                                  jump_url=jump_url)

            pics.save()

        return Response({"code": 0, "info": ""})

    @list_route(methods=['get'])
    def get_promotion_topic_pics(self, request, **kwargs):
        from flashsale.coupon.models import UserCoupon
        from flashsale.promotion.views import get_customer
        customer = get_customer(request)
        content = request.REQUEST
        act_id = content.get("promotion_id", None)

        if act_id:
            #some customer visit http://m.xiaolumeimei.com/mall/activity/topTen/model/2?ufrom=wx&id=87%3F10000skip%3Dtrue&mm_linkid=23952
            #id is wrong,so must avoid it
            if not (str(act_id).isdigit()):
                act_arr = re.findall(r'\d+', str(act_id))
                if not act_arr:
                    return Response({})
                act_id = act_arr[0]
            act = ActivityEntry.objects.filter(id=act_id).order_by('-start_time').first()
        else:
            act = ActivityEntry.objects.filter(is_active=True).order_by('-start_time').first()

        if not act:
            return Response({"code": 1, "info": "推广活动不存在,请先创建"})

        desc_pics = act.activity_products.order_by('location_id').values(
            'id', 'model_id', 'product_img', 'product_name', 'pic_type', 'jump_url')
        model_products = ModelProductCtl.multiple([p['model_id'] for p in desc_pics if p['model_id']])
        models_dict = dict([(mp.id, mp) for mp in model_products])
        type_pics_dict = defaultdict(list)
        for pic in desc_pics:
            mp = models_dict.get(pic['model_id'])
            if mp:
                pic.update({
                    'lowest_agent_price':mp.detail_content.get('lowest_agent_price'),
                    'lowest_std_sale_price': mp.detail_content.get('lowest_std_sale_price'),
                })
            type_pics_dict[pic['pic_type']].append(pic)

        banners = type_pics_dict.get(ActivityProduct.BANNER_PIC_TYPE, [])
        banner_pic = banners[0]['product_img'] if banners else ''

        coupon_getbefore_pic = type_pics_dict.get(ActivityProduct.COUPON_GETBEFORE_PIC_TYPE,[])
        coupon_getafter_pic  = type_pics_dict.get(ActivityProduct.COUPON_GETAFTER_PIC_TYPE,[])
        if len(coupon_getafter_pic) != len(coupon_getbefore_pic):
            return Response({"code": 2, "info": "优惠券领前,领后数目不一致"})

        coupon_getafter_pic_dict = dict([(p['model_id', p]) for p in coupon_getafter_pic])
        user_coupon_template_ids = []
        if customer:
            user_coupon_template_ids = UserCoupon.objects.filter(customer_id=customer.id)\
                .values_list('template_id', flat=True)

        coupons = []
        for coupon in coupon_getbefore_pic:
            isReceived = int(coupon['model_id']) in user_coupon_template_ids
            coupon_dict = {
                "couponId": coupon['model_id'],
                "getBeforePic": coupon['product_img'],
                "getAfterPic":coupon_getafter_pic_dict.get(coupon['model_id'])['product_img'],
                "jumpUrl": coupon['jump_url'],
                "isReceived": isReceived
            }
            coupons.append(coupon_dict)

        topics = []
        topics_pic = type_pics_dict.get(ActivityProduct.TOPIC_PIC_TYPE, [])
        for topic in topics_pic:
            if (topic['product_img']) and (len(topic['product_img']) != 0):
                topic_dict = {"pic": topic['product_img'], "jumpUrl": topic['jump_url']}
                topics.append(topic_dict)

        categorys = type_pics_dict.get(ActivityProduct.CATEGORY_PIC_TYPE, [])
        category_pic = categorys and categorys[0]['product_img'] or ''

        shares = type_pics_dict.get(ActivityProduct.FOOTER_PIC_TYPE, [])
        share_pic = shares and shares[0]['product_img'] or ''

        goods_horizon_pic = type_pics_dict.get(ActivityProduct.GOODS_HORIZEN_PIC_TYPE, [])
        goods_horizon = []
        for goods in goods_horizon_pic:
            goods_dict = {"modelId": goods['model_id'], "pic": goods['product_img'], "productName": goods['product_name'],
                          "lowestPrice": goods['lowest_agent_price'], "stdPrice": goods['lowest_std_sale_price']}
            goods_horizon.append(goods_dict)

        goods_vertical_pic = type_pics_dict.get(ActivityProduct.GOODS_VERTICAL_PIC_TYPE, [])
        goods_vertical = []
        for goods in goods_vertical_pic:
            goods_dict = {"modelId": goods['model_id'], "pic": goods['product_img'], "productName": goods['product_name'],
                          "lowestPrice": goods['lowest_agent_price'], "stdPrice": goods['lowest_std_sale_price']}
            goods_vertical.append(goods_dict)

        return_dict = {"title": act.title,
                       "activityId": act.id, "banner": banner_pic,
                       "coupons": coupons, "topics": topics,
                       "category": category_pic, "shareBtn": share_pic,
                       "productsHorizental": goods_horizon, "productsVertical": goods_vertical}
        if desc_pics:
            return Response(return_dict)
        else:
            return Response({})
