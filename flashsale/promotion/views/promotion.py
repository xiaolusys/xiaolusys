# -*- coding:utf-8 -*-
import datetime
import json
import logging
import os
import re
import urlparse

from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum, Q
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.views.generic import View
from rest_framework import permissions, authentication
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils.modelutils import update_model_fields
from core.weixin.mixins import WeixinAuthMixin
from core.weixin.signals import signal_weixin_snsauth_response
from flashsale.coupon.models import UserCoupon
from flashsale.pay.models import Customer
from flashsale.promotion.models import XLInviteCode, XLReferalRelationship
from flashsale.promotion.models import XLSampleApply, XLFreeSample, XLSampleOrder, ReadPacket
from flashsale.xiaolumm.models.models_fans import XlmmFans

logger = logging.getLogger('django.request')

CARTOON_DIGIT_IMAGES = [
    "http://7xogkj.com2.z0.glb.qiniucdn.com/222-0.png",
    "http://7xogkj.com2.z0.glb.qiniucdn.com/222-1.png",
    "http://7xogkj.com2.z0.glb.qiniucdn.com/222-2.png",
    "http://7xogkj.com2.z0.glb.qiniucdn.com/222-3.png",
    "http://7xogkj.com2.z0.glb.qiniucdn.com/222-4.png",
    "http://7xogkj.com2.z0.glb.qiniucdn.com/222-5.png",
    "http://7xogkj.com2.z0.glb.qiniucdn.com/222-6.png",
    "http://7xogkj.com2.z0.glb.qiniucdn.com/222-7.png",
    "http://7xogkj.com2.z0.glb.qiniucdn.com/222-8.png",
    "http://7xogkj.com2.z0.glb.qiniucdn.com/222-9.png"
]


def get_cartoon_digit(n):
    n = int(n) % 10
    return CARTOON_DIGIT_IMAGES[n]


def get_active_pros_data():
    """
    获取活动产品数据　　
    返回活动产品对象
    """
    free_samples = (1,)  # 指定id的产品
    queryset = XLFreeSample.objects.filter(id__in=free_samples)  # 要加入活动的产品
    if queryset.exists():
        return queryset[0]
    return None


def get_product_img(sku_code):
    """ 获取用户颜色
    1: yellow
    2: blue
    3: pink
    """
    try:
        sku_code = int(sku_code)
    except:
        sku_code = 0
    yellowbag = "http://7xogkj.com2.z0.glb.qiniucdn.com/222-bag-yellow.png"
    bluebag = "http://7xogkj.com2.z0.glb.qiniucdn.com/222-bag-blue.png"
    pinkbag = "http://7xogkj.com2.z0.glb.qiniucdn.com/222-bag-pink.png"
    img = ['', yellowbag, bluebag, pinkbag]
    return img[sku_code] if sku_code in (1, 2, 3) else yellowbag


def get_customer_apply(**kwargs):
    """
    获取用户的试用申请
    """
    mobile = kwargs.get('mobile', None)
    user_openid = kwargs.get('openid', None)
    if mobile:
        xls = XLSampleApply.objects.filter(mobile=mobile).order_by('-created')  # 记录来自平台设申请的sku选项
        if xls.exists():
            return xls[0]
    if user_openid:
        xls = XLSampleApply.objects.filter(user_openid=user_openid).order_by('-created')  # 记录来自平台设申请的sku选项
        if xls.exists():
            return xls[0]
    return None


def get_customer(request):
    """
    根据http request 对象　返回 特卖用户，不存在则返回None, 存在返回用户对象
    """
    user = request.user
    if not user or user.is_anonymous():
        return None
    try:
        customer = Customer.objects.get(user_id=request.user.id)
    except Customer.DoesNotExist:
        customer = None
    return customer

from shopapp.weixin.options import get_openid_by_unionid
class XLSampleapplyView(WeixinAuthMixin, View):
    xlsampleapply = 'promotion/apply.html'

    vipcode_default_message = u'请输入邀请码'
    vipcode_error_message = u'邀请码不正确'
    mobile_default_message = u''
    mobile_error_message = u'手机号码有误'

    PLANTFORM = ('wxapp', 'pyq', 'qq', 'sinawb', 'web', 'qqspa', 'app')

    def get_openid_and_unionid_by_customer(self, request):
        customer = get_customer(request)
        if not customer:
            return '', ''
        openid = get_openid_by_unionid(customer.unionid, settings.WXPAY_APPID)
        return openid, customer.unionid

    def get(self, request):
        content = request.GET
        customer = get_customer(request)
        mobile = customer.mobile if customer else None

        vipcode = content.get('vipcode', None)  # 获取分享用户　用来记录分享状况
        from_customer = content.get('from_customer', '1')  # 分享人的用户id
        openid = content.get('openid', None)  # 获取分享用户　用来记录分享状况
        if from_customer is not None and not from_customer.isdigit():
            raise Http404('404')
        active_start = False
        wxprofile = {}
        if self.is_from_weixin(request):  # 如果是在微信里面
            openid, unionid = self.get_cookie_openid_and_unoinid(request)

            if not self.valid_openid(openid) or not self.valid_openid(unionid):
                wxprofile = self.get_auth_userinfo(request)
                openid, unionid = wxprofile.get("openid"), wxprofile.get("unionid")

            if not self.valid_openid(openid) or not self.valid_openid(unionid):  # 若果是无效的openid则跳转到授权页面
                return redirect(self.get_snsuserinfo_redirct_url(request))

            if wxprofile:
                signal_weixin_snsauth_response.send(sender="snsauth", appid=self._wxpubid, resp_data=wxprofile)
        else:
            openid, unionid = self.get_openid_and_unionid_by_customer(request)

        referal = Customer.objects.normal_customer.filter(id=from_customer).first()
        title = u'小鹿美美邀您闹元宵'

        # 商品sku信息  # 获取商品信息到页面
        pro = get_active_pros_data()  # 获取活动产品数据
        xls = get_customer_apply(**{"openid": openid, "mobile": mobile})
        if xls:
            img_src = get_product_img(xls.sku_code)  # 获取sku图片
            download = True
        else:
            download = False
            img_src = get_product_img(0)  # 获取默认图片图片
        response = render_to_response(self.xlsampleapply,
                                      {"active_start": active_start,
                                       "vipcode": vipcode,
                                       "from_customer": from_customer,
                                       "pro": pro,
                                       "openid": openid,
                                       "wxprofile": wxprofile,
                                       "referal": referal,
                                       "title": title, "mobile": mobile,
                                       "download": download,
                                       "img_src": img_src,
                                       "mobile_message": self.mobile_default_message},
                                      context_instance=RequestContext(request))
        if self.is_from_weixin(request):
            self.set_cookie_openid_and_unionid(response, openid, unionid)

        return response

    def post(self, request):
        content = request.POST
        vmobile = content.get("mobile", None)  # 参与活动的手机号
        vipcode = content.get("vipcode", None)  # 活动邀请码

        from_customer = content.get('from_customer') or '1'  # 分享人的用户id
        outer_id = content.get('outer_id', None)
        sku_code = content.get("sku_code", None)  # 产品sku码
        ufrom = content.get("ufrom", None)
        agent = request.META.get('HTTP_USER_AGENT', None)  # 获取浏览器类型
        # openid, unionid = self.get_openid_and_unionid(request)  # 获取用户的openid, unionid
        openid = content.get('openid', None)  # 获取提交的openid

        pro = get_active_pros_data()  # 获取活动产品数据

        regex = re.compile(r'^1[34578]\d{9}$', re.IGNORECASE)
        mobiles = re.findall(regex, vmobile)
        mobile = mobiles[0] if len(mobiles) >= 1 else None

        if not mobile:
            return render_to_response(self.xlsampleapply,
                                      {"vipcode": vipcode,
                                       "pro": pro,
                                       "mobile": vmobile,
                                       "mobile_message": self.mobile_error_message},
                                      context_instance=RequestContext(request))

        xls = get_customer_apply(**{"mobile": mobile, 'openid': openid})
        if not xls:  # 如果没有申请记录则创建记录
            sample_apply = XLSampleApply()
            for k, v in content.iteritems():
                if hasattr(sample_apply, k):
                    setattr(sample_apply, k, v)
            if not sample_apply.from_customer:
                sample_apply.from_customer = from_customer
            sample_apply.save()
            img_src = get_product_img(sample_apply.sku_code)  # 获取sku图片
            # 生成自己的邀请码
            # expiried = datetime.datetime(2016, 2, 29, 0, 0, 0)
            # XLInviteCode.objects.genVIpCode(mobile=mobile, expiried=expiried)

            cust = Customer.objects.normal_customer.filter(id=from_customer).first()  # 用户是否存在
            # cust = custs[0] if custs.exists() else ''
            # if cust:  # 给分享人（存在）则计数邀请数量
            # participates = XLInviteCode.objects.filter(mobile=cust.mobile)
            # if participates.exists():
            # participate = participates[0]
            # participate.usage_count += 1
            # participate.save()  # 使用次数累加
            if ufrom == 'app':
                # 如果用户来自app内部则跳转到活动激活页面
                url = '/sale/promotion/xlsampleorder/'
                return redirect(url)
        else:
            if ufrom == 'app':  # 如果存在订单并且是app来的就跳转到激活页面
                # 如果用户来自app内部则跳转到活动激活页面
                url = '/sale/promotion/xlsampleorder/'
                return redirect(url)
            img_src = get_product_img(xls.sku_code)  # 获取sku图片
        return render_to_response(self.xlsampleapply,
                                  {"vipcode": vipcode, "pro": pro, "img_src": img_src,
                                   "mobile": vmobile, "download": True},
                                  context_instance=RequestContext(request))


from common.utils import valid_mobile
from shopapp.weixin.models_base import WeixinUserInfo


class APPDownloadView(WeixinAuthMixin, View):
    """ 下载页面 """
    download_page = 'promotion/download.html'
    QQ_YINYONGBAO_URL = 'http://a.app.qq.com/o/simple.jsp?pkgname=com.jimei.xiaolumeimei'  # 腾讯应用宝下载跳转链接

    def get_current_customer(self, unionid=None, mobile=None):
        """
        获取当前访问用户
        """
        return Customer.objects.normal_customer.filter(Q(unionid=unionid) | Q(mobile=mobile)).first()

    def get(self, request):
        content = request.GET
        from_customer = content.get('from_customer') or ''  # 分享人的用户id
        if not from_customer:
            mm_linkid = content.get('mm_linkid') or None  # 分享人的用户id
            if mm_linkid is None:
                cookies = request.COOKIES
                mm_linkid = cookies.get("mm_linkid")
            from flashsale.xiaolumm.models import XiaoluMama
            mm = XiaoluMama.objects.filter(id=mm_linkid).first()
            if mm:
                customer = mm.get_mama_customer()
                from_customer = str(customer.id) if customer else ''

        mobile = content.get('mobile') or ''
        ufrom = content.get("ufrom") or None
        diff_customer = True
        userinfo = {}

        from flashsale.promotion.tasks_activity import task_create_appdownloadrecord_with_userinfo, \
            task_create_appdownloadrecord_with_mobile
        if from_customer.isdigit():
            if self.is_from_weixin(request):
                self.set_appid_and_secret(settings.WXPAY_APPID, settings.WXPAY_SECRET)

                # get openid from cookie
                openid, unionid = self.get_cookie_openid_and_unoinid(request)

                if unionid:
                    record = WeixinUserInfo.objects.filter(unionid=unionid).first()
                    if record:
                        userinfo.update({"unionid":record.unionid, "nickname":record.nick, "headimgurl":record.thumbnail})

                if not userinfo:
                    # get openid from 'debug' or from using 'code' (if code exists)
                    userinfo = self.get_auth_userinfo(request)
                    unionid = userinfo.get("unionid")

                    if not self.valid_openid(unionid):
                        logger.warn("Appdownloadview| invalid unionid: %s" % unionid)

                    if not unionid:
                        # if we still dont have openid, we have to do oauth
                        redirect_url = self.get_snsuserinfo_redirct_url(request)
                        logger.warn("AppDownloadView|redirect_url: %s, absolute_uri:%s" %(redirect_url, request.build_absolute_uri()))
                        return redirect(redirect_url)
                # now we have userinfo

                request_customer = self.get_current_customer(unionid=unionid)
                if from_customer.isdigit() and request_customer and request_customer.id == int(from_customer):
                    diff_customer = False

                if from_customer.isdigit() and diff_customer:
                    task_create_appdownloadrecord_with_userinfo.delay(from_customer, userinfo)
            elif valid_mobile(mobile):
                request_customer = self.get_current_customer(mobile=mobile)
                if from_customer.isdigit() and request_customer and request_customer.id == int(from_customer):
                    diff_customer = False

                if from_customer.isdigit() and diff_customer:
                    task_create_appdownloadrecord_with_mobile.delay(from_customer, mobile)

        agent = request.META.get('HTTP_USER_AGENT', None)  # 获取浏览器类型
        if agent and ("MicroMessenger" in agent or 'iPhone' in agent):  # 如果是微信或者是iphone则跳转到应用宝下载
            url = self.QQ_YINYONGBAO_URL
            return redirect(url)
        return redirect('/static/promotion/html/download.html')


from flashsale.promotion.models import XLInviteCount


class XlSampleOrderView(View):
    """
    免费申请试用活动，生成正式订单页面
    """
    order_page = 'promotion/xlsampleorder.html'
    share_link = 'sale/promotion/xlsampleapply/?from_customer={customer_id}'
    PROMOTION_LINKID_PATH = 'pmt'
    PROMOTE_CONDITION = 20

    def get_promotion_result(self, customer_id, outer_id, mobile, sample_order):
        """ 返回自己的用户id　　返回邀请结果　推荐数量　和下载数量 """
        inv_count, state = XLInviteCount.objects.get_or_create(customer_id=customer_id)
        promote_count = inv_count.apply_count  # 邀请的数量
        # 是否可以购买睡袋　邀请数量达到要求即可以跳转购买睡袋
        vipcode = None
        # 下载appd 的数量(激活的数量)
        app_down_count = inv_count.invite_count

        second_num = app_down_count % 10
        first_num = (app_down_count % 100 - second_num) / 10
        first_digit_imgsrc = get_cartoon_digit(first_num)
        second_digit_imgsrc = get_cartoon_digit(second_num)

        inactive_count = inv_count.apply_count - inv_count.invite_count
        active_count = inv_count.invite_count
        share_link = self.share_link.format(**{'customer_id': customer_id})
        # 用户活动红包
        reds = self.my_red_packets(customer_id)
        reds_money = reds.aggregate(sum_value=Sum('value')).get('sum_value') or 0
        res = {'promote_count': promote_count,
               'first_digit_imgsrc': first_digit_imgsrc,
               "reds": reds,
               "reds_money": reds_money,
               'second_digit_imgsrc': second_digit_imgsrc,
               "inactive_count": inactive_count,
               "active_count": active_count,
               'share_link': share_link,
               'link_qrcode': '',
               "vipcode": vipcode,
               'invite_pass': sample_order.is_sampleorder_pass(),
               'award_receive': sample_order.is_award_complete()}
        return res

    def handler_with_vipcode(self, vipcode, mobile, outer_id, sku_code, customer):
        xlcodes = XLInviteCode.objects.filter(vipcode=vipcode)

        if xlcodes.exists():  # 邀请码对应的邀请人存在
            xlcode = xlcodes[0]
            from_mobile = xlcode.mobile
            customers = Customer.objects.filter(mobile=from_mobile, status=Customer.NORMAL)
            if customers.exists():  # 推荐人用户存在
                from_customer = customers[0].id
                expiried = datetime.datetime(2016, 2, 29, 0, 0, 0)
                # 生成自己的邀请码
                try:
                    xincode = XLInviteCode.objects.get(mobile=mobile)
                    new_vipcode = xincode.vipcode
                except XLInviteCode.DoesNotExist:
                    new_vipcode = XLInviteCode.objects.genVIpCode(mobile=mobile, expiried=expiried)
                # 生成自己申请记录
                new_xlapply = XLSampleApply.objects.create(outer_id=outer_id, sku_code=sku_code,
                                                           from_customer=from_customer, mobile=mobile,
                                                           vipcode=new_vipcode,
                                                           status=XLSampleApply.ACTIVED)
                xlcode.usage_count += 1  # 推荐人的邀请码使用次数加１
                xlcode.save()
                # 生成自己的正式订单
                sample_order = XLSampleOrder.objects.create(xlsp_apply=new_xlapply.id,
                                                            customer_id=customer.id,
                                                            outer_id=outer_id, sku_code=sku_code)
                res = self.get_promotion_result(customer.id, outer_id, mobile, sample_order)

                referal_uid = customer.id  # 被推荐人ID
                referal_from_uid = from_customer  # 推荐人ID
                XLReferalRelationship.objects.get_or_create(referal_uid=str(referal_uid),
                                                            referal_from_uid=str(referal_from_uid))
                # 记录粉丝
                XlmmFans.objects.createFansRecord(referal_from_uid, referal_uid)
                # 给推荐人发红包
                self.release_packet_for_refreal(from_customer)
        else:
            res = None
        return res

    def release_packet_for_refreal(self, refreal_from):
        """
        给推荐人发红包, 首次有激活发送红包，　以后每增加３个激活　发送一个红包
        """
        refreal_from = str(refreal_from)
        # 计算推荐人的下载激活数量
        active_count = XLSampleApply.objects.filter(from_customer=refreal_from,
                                                    status=XLSampleApply.ACTIVED).count()  # 推荐人的邀请记录
        # app_down_count = XLSampleOrder.objects.filter(xlsp_apply__in=applys.values('id')).count()  # 推荐人的激活记录
        ReadPacket.objects.release133_packet(refreal_from, active_count)

    def my_red_packets(self, customer):
        """
        用户活动红包
        """
        reds = ReadPacket.objects.filter(customer=customer)
        return reds

    def active_order(self, xlapply, customer, outer_id, sku_code):
        """
        激活申请：
        1.生成订单记录
        2.生成邀请关系记录
        3.记录粉丝列表信息
        4.给推荐人发红包
        """
        sample_orders = XLSampleOrder.objects.filter(xlsp_apply=xlapply.id, customer_id=customer.id)
        if sample_orders.exists():
            return sample_orders[0]
        xlorder = XLSampleOrder.objects.create(xlsp_apply=xlapply.id, customer_id=customer.id,
                                               outer_id=outer_id, sku_code=sku_code)
        # 生成邀请关系记录
        referal_uid = customer.id  # 被推荐人ID
        referal_from_uid = xlapply.from_customer  # 推荐人ID
        XLReferalRelationship.objects.get_or_create(referal_uid=str(referal_uid),
                                                    referal_from_uid=str(referal_from_uid))
        xlapply.status = XLSampleApply.ACTIVED  # 激活预申请中的字段
        xlapply.save()

        # 记录粉丝列表信息
        XlmmFans.objects.createFansRecord(xlapply.from_customer, customer.id)
        # 给推荐人发红包
        self.release_packet_for_refreal(referal_from_uid)
        # 检查用户头像昵称
        if xlapply.headimgurl and xlapply.nick:
            customer.nick = xlapply.nick
            customer.thumbnail = xlapply.headimgurl
            update_model_fields(customer, update_fields=['nick', 'thumbnail'])

        return xlorder

    def get(self, request):
        title = "元宵好兆头 抢红包 赢睡袋"
        pro = get_active_pros_data()  # 获取活动产品数据
        # 如果用户已经有正式订单存在 则 直接返回分享页
        customer = get_customer(request)
        mobile = customer.mobile if customer else None
        active_start = False
        if customer:
            outer_id = pro.outer_id
            sample_order = None
            xls_orders = XLSampleOrder.objects.filter(customer_id=customer.id).order_by('-created')
            if xls_orders.exists():
                sample_order = xls_orders[0]
                customer_id = customer.id
                mobile = customer.mobile
                sku_code = xls_orders[0].sku_code
                img_src = get_product_img(sku_code)
                res = self.get_promotion_result(customer_id, outer_id, mobile, sample_order)
            else:
                # 查找存在的申请，　如果有存在的申请则直接为用户激活
                xlapply = get_customer_apply(**{"mobile": mobile})
                res = None
                img_src = get_product_img(None)
                if xlapply:  # 有申请
                    sample_order = self.active_order(xlapply, customer, outer_id, xlapply.sku_code)
                    img_src = get_product_img(xlapply.sku_code)
                    customer_id = sample_order.customer_id
                    res = self.get_promotion_result(customer_id, outer_id, mobile, sample_order)
                else:
                    # 如果当前用户没有申请过则跳转到申请页面并且指定来自平台，和推荐用户
                    url = '/sale/promotion/xlsampleapply/?ufrom=app&from_customer=1'
                    return redirect(url)

            return render_to_response(self.order_page,
                                      {"pro": pro,
                                       "res": res,
                                       "title": title,
                                       "img_src": img_src,
                                       "active_start": active_start,
                                       "sample_order": sample_order
                                       },
                                      context_instance=RequestContext(request))
        return render_to_response(self.order_page, {"pro": pro, "title": title},
                                  context_instance=RequestContext(request))

    def post(self, request):
        content = request.POST
        customer = get_customer(request)
        outer_id = content.get('outer_id', None)
        sku_code = content.get('sku_code', 0)
        vipcode = content.get('vipcode', None)

        mobile = customer.mobile if customer else None
        pro = get_active_pros_data()  # 获取活动产品数据
        title = "活动正式订单"
        if mobile is None:
            error_message = "请验证手机"
            return render_to_response(self.order_page,
                                      {
                                          "pro": pro,
                                          "title": title,
                                          "error_message": error_message
                                      },
                                      context_instance=RequestContext(request))  # 缺少参数
        xlapply = get_customer_apply(**{"mobile": mobile})
        if xlapply:  # 有　试用申请　记录的
            # 激活申请
            xlorder = self.active_order(xlapply, customer, outer_id, sku_code)
            outer_ids = ['', ]
            outer_ids[0] = outer_id
            res = self.get_promotion_result(customer.id, outer_ids, mobile, xlorder)
            return render_to_response(self.order_page, {"pro": pro, "res": res},
                                      context_instance=RequestContext(request))

        not_apply_message = "您还没有试用申请，请先申请再激活．．．"
        return render_to_response(self.order_page, {"pro": pro,
                                                    "title": title,
                                                    "not_apply": not_apply_message},
                                  context_instance=RequestContext(request))


class CusApplyOrdersView(APIView):
    """
     获取用户的推荐申请　和　激活　信息
    """
    promote_condition = 'promotion/friendlist.html'

    def get(self, request):
        customer = get_customer(request)
        customer_id = customer.id if customer else 0
        applys = XLSampleApply.objects.filter(from_customer=customer_id).exclude(user_openid='')
        apply_results = applys.values('headimgurl', 'nick', 'created', 'status')
        return render_to_response(self.promote_condition, {'apply_results': apply_results},
                                  context_instance=RequestContext(request))


def update_red_packet():
    """ 修复bug 跟新活动红包到没有兑换状态　"""
    reds = ReadPacket.objects.filter(status=ReadPacket.EXCHANGE)
    print "条数:", reds.count()
    reds.update(status=ReadPacket.NOT_EXCHANGE)
    return


class ExchangeRedToCoupon(APIView):
    """
    将用户活动红包兑换成优惠券
    """

    def get_red_ids(self, request):
        """
        获取请求中的红包id
        """
        ids = request.POST.getlist('ids')

        try:
            ids = [int(i) for i in ids]
        except:
            return []
        return ids

    def exchange_redpackets(self, ids=None, customer=None):
        code = 0
        reds = ReadPacket.objects.filter(id__in=ids, customer=customer, status=ReadPacket.NOT_EXCHANGE)
        sum_value = reds.aggregate(s_v=Sum('value')).get('s_v') or 0
        reds_count = reds.count()  # 红包条数
        if reds_count <= 0:  # 如果红包个数小于0则直接返回
            return 2, 0, 0
        coupon_10_count = int(sum_value / 10)  # 十元优惠券条数
        leave_mony = sum_value - coupon_10_count * 10  # 发完十元后还剩下多少钱
        if leave_mony > 0:
            coupon_5_count = 1 if leave_mony / 5 < 1 else 2  # 剩下的红包金额除以5　大于１则发送2张５元优惠券　否则发放１张优惠券
        else:
            coupon_5_count = 0
        code = ''
        for i in range(coupon_10_count):
            cou, code, msg = UserCoupon.objects.create_normal_coupon(buyer_id=customer, template_id=21)
        for j in range(coupon_5_count):
            cou, code, msg = UserCoupon.objects.create_normal_coupon(buyer_id=customer, template_id=20)
        if code == 0 or code == 0:
            reds.update(status=ReadPacket.EXCHANGE)  # 更新红包到兑换状态
        coupon_value = coupon_10_count * 10 + coupon_5_count * 5
        return code, coupon_10_count + coupon_5_count, coupon_value

    def post(self, request):
        """
        code : 0 兑换成功
        code : 1 没有注册用户
        code : 2 没有满足兑换条件
        """
        code = 0
        customer = get_customer(request)
        customer_id = str(customer.id) if customer else customer
        # 获取红包id
        ids = self.get_red_ids(request)
        res = None
        if ids:
            code, count, coupon_value = self.exchange_redpackets(ids=ids, customer=customer_id)
            res = {"code": code, 'count': count, "coupon_value": coupon_value}
        return HttpResponse(json.dumps(res))


class PromotionResultMixin(object):
    def get_orders(self, month=None, batch=None):
        """
        根据月份和批次获取活动的中奖名单，pass_num:表示满足的中奖条件(激活数)
        """
        order_list = XLSampleOrder.objects.none()
        if month == 1602:
            start_time = datetime.datetime(2016, 2, 22)
            end_time = datetime.datetime(2016, 3, 1)
            order_list = XLSampleOrder.objects.filter(created__range=(start_time, end_time), status=batch)

        return order_list

    def get_date_tuple(self, item):
        customer = Customer.objects.get(id=item.customer_id)
        inv_cnt = XLInviteCount.objects.get(customer_id=item.customer_id)

        mobile = ''.join([customer.mobile[0:3], "****", customer.mobile[7:11]])
        thumbnail = customer.thumbnail or 'http://7xogkj.com2.z0.glb.qiniucdn.com/Icon-60%402x.png'  # 小鹿logo缺省头像
        res = (mobile, inv_cnt.invite_count, inv_cnt.apply_count, thumbnail)
        return res


class PromotionShortResult(PromotionResultMixin, APIView):
    def get(self, request):
        items = []
        order_list = self.get_orders(None, None)
        customer_ids = [item.customer_id for item in order_list]
        wx_users = Customer.objects.normal_customer.filter(id__in=customer_ids)
        for user in wx_users:
            items.append(self.get_date_tuple(user))
        return HttpResponse(json.dumps(items))


class PromotionResult(PromotionResultMixin, APIView):
    """ 活动中奖结果展示 """

    # permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = ()
    # renderer_classes = (renderers.TemplateHTMLRenderer, renderers.BrowsableAPIRenderer,)
    template_name = 'promotion/pmt_result.html'

    def get(self, request, *args, **kwargs):
        page = int(kwargs.get('page', 1))
        batch = int(kwargs.get('batch', 1))
        month = int(kwargs.get('month', 1))
        order_list = self.get_orders(month=month, batch=batch)
        num_per_page = 20  # Show 20 contacts per page
        paginator = Paginator(order_list, num_per_page)

        try:
            result_page = paginator.page(page)
        except PageNotAnInteger:  # If page is not an integer, deliver first page.
            result_page = paginator.page(1)
        except EmptyPage:  # If page is out of range (e.g. 9999), deliver last page of results.
            result_page = paginator.page(paginator.num_pages)

        items = []
        for item in result_page:
            items.append(self.get_date_tuple(item))

        total = order_list.count()  # 总条数
        num_pages = paginator.num_pages  # 当前页

        next_page = min(page + 1, num_pages)
        prev_page = max(page - 1, 1)
        res = {"items": items, 'num_pages': num_pages,
               'total': total, 'num_per_page': num_per_page,
               'prev_page': prev_page, 'next_page': next_page,
               'page': page, 'batch': batch, 'month': month}
        print 'debug res:', res['items']
        return Response(res)


class ReceiveAwardView(PromotionResultMixin, APIView):
    """
    活动中奖结果展示
    """
    result_page = 'promotion/pmt_result.html'
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (renderers.JSONRenderer,)

    def post(self, request, *args, **kwargs):
        sampleorder_id = request.POST.get('sampleorder_id')
        sampleorder = get_object_or_404(XLSampleOrder, id=sampleorder_id)
        if sampleorder.is_award_complete():
            return Response({'code': 1, 'message': '已领取优惠券.'})
        sampleorder.award_confirm()
        return Response({'code': 0, 'message': '领取成功!'})


class QrCodeView(APIView):
    """
    得到个人专属二维码以便分享
    """
    template = "promotion/qrcode.html"
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (renderers.BrowsableAPIRenderer,)

    share_link = 'sale/promotion/xlsampleapply/?from_customer={customer_id}&ufrom={ufrom}'
    PROMOTION_LINKID_PATH = 'qrcode/promote'

    def get_share_link(self, params):
        link = urlparse.urljoin(settings.M_SITE_URL, self.share_link)
        return link.format(**params)

    def gen_custmer_share_qrcode_pic(self, customer_id, ufrom):
        params = {'customer_id': customer_id, "ufrom": ufrom}
        file_name = os.path.join(self.self.PROMOTION_LINKID_PATH,
                                 'custom-{customer_id}-{ufrom}.jpg'.format(**params))
        share_link = self.get_share_link(params)

        from core.upload.xqrcode import push_qrcode_to_remote

        qrcode_url = push_qrcode_to_remote(file_name, share_link)

        return qrcode_url

    def get(self, request, *args, **kwargs):
        customer = get_customer(request)
        qrimg = self.gen_custmer_share_qrcode_pic(customer.id, 'wxapp')
        data = {"qrimg": qrimg, "thumbnail": customer.thumbnail, "nick": customer.nick}
        response = render_to_response(self.template, data, context_instance=RequestContext(request))
        return response


