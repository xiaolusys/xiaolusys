# -*- coding:utf-8 -*-
import os, settings, urlparse
import datetime
import re
import json
import random

from django.views.generic import View
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.forms import model_to_dict
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from rest_framework.views import APIView
from rest_framework import permissions, authentication
from rest_framework.renderers import BrowsableAPIRenderer

from flashsale.restpro.options import gen_and_save_jpeg_pic
from core.weixin.mixins import WeixinAuthMixin
from core.weixin.signals import signal_weixin_snsauth_response
from core.weixin.options import set_cookie_openid

from flashsale.pay.models import Customer
from shopapp.weixin.views import get_user_openid, valid_openid
from .models_freesample import XLSampleApply, XLFreeSample, XLSampleSku, XLSampleOrder, ReadPacket
from .models import XLInviteCode, XLReferalRelationship
from flashsale.xiaolumm.models_fans import XlmmFans


def genCode():
    NUM_CHAR_LIST = list('1234567890')
    return ''.join(random.sample(NUM_CHAR_LIST, 7))


def get_active_pros_data():
    free_samples = (1, 2)
    queryset = XLFreeSample.objects.filter(id__in=free_samples)  # 要加入活动的产品
    if queryset.exists():
        return queryset[0]
    return None


class XLSampleapplyView(WeixinAuthMixin, View):
    xlsampleapply = 'promotion/apply.html'

    vipcode_default_message = u'请输入邀请码'
    vipcode_error_message = u'邀请码不正确'
    mobile_default_message = u'请输入手机号'
    mobile_error_message = u'手机号码有误'

    PLANTFORM = ('wxapp', 'pyq', 'qq', 'sinawb', 'web', 'qqspa')

    def get(self, request):
        content = request.REQUEST
        vipcode = content.get('vipcode', None)  # 获取分享用户　用来记录分享状况
        agent = request.META.get('HTTP_USER_AGENT', None)  # 获取浏览器类型
        from_customer = content.get('from_customer', 0)  # 分享人的用户id
        if self.is_from_weixin(request):  # 如果是在微信里面
            res = self.get_auth_userinfo(request)
            openid = res.get("openid")
            unionid = res.get("unionid")

            if not self.valid_openid(openid):  # 若果是无效的openid则跳转到授权页面
                return redirect(self.get_snsuserinfo_redirct_url(request))

            signal_weixin_snsauth_response.send(sender="snsauth", appid=self._wxpubid, resp_data=res)

        cus = Customer.objects.filter(id=from_customer)
        referal = cus[0] if cus.exists() else None


        # 商品sku信息  # 获取商品信息到页面
        pro = get_active_pros_data()  # 获取活动产品数据
        response = render_to_response(self.xlsampleapply,
                                      {"vipcode": vipcode,
                                       "from_customer": from_customer,
                                       "pro": pro,
                                       "referal": referal,
                                       "mobile_message": self.mobile_default_message},
                                      context_instance=RequestContext(request))
        if self.is_from_weixin(request):
            set_cookie_openid(response, self._wxpubid, openid, unionid)

        return response

    def post(self, request):
        content = request.REQUEST
        vmobile = content.get("mobile", None)  # 参与活动的手机号
        vipcode = content.get("vipcode", None)  # 活动邀请码
        from_customer = content.get('from_customer') or 0  # 分享人的用户id
        outer_id = content.get('outer_id', None)
        sku_code = content.get("sku_code", None)  # 产品sku码
        ufrom = content.get("ufrom", None)
        openid = None
        agent = request.META.get('HTTP_USER_AGENT', None)  # 获取浏览器类型
        openid, unionid = self.get_openid_and_unionid(request)  # 获取用户的openid, unionid

        pro = get_active_pros_data()  # 获取活动产品数据

        regex = re.compile(r'^1[34578]\d{9}$', re.IGNORECASE)
        mobiles = re.findall(regex, vmobile)
        mobile = mobiles[0] if len(mobiles) >= 1 else None

        if mobile:
            xls = XLSampleApply.objects.filter(outer_id=outer_id, mobile=mobile)  # 记录来自平台设申请的sku选项
            if not xls.exists():  # 如果没有申请记录则创建记录
                sku_code_r = '' if sku_code is None else sku_code
                sample_apply = XLSampleApply()
                sample_apply.outer_id = outer_id
                sample_apply.mobile = mobile
                sample_apply.sku_code = sku_code_r
                sample_apply.vipcode = vipcode
                sample_apply.user_openid = openid
                sample_apply.from_customer = from_customer  # 保存分享人的客户id
                if ufrom in self.PLANTFORM:
                    sample_apply.ufrom = ufrom
                sample_apply.save()

                # 生成自己的邀请码
                expiried = datetime.datetime(2016, 2, 29, 0, 0, 0)
                XLInviteCode.objects.genVIpCode(mobile=mobile, expiried=expiried)

                custs = Customer.objects.filter(id=from_customer)  # 用户是否存在
                cust = custs[0] if custs.exists() else ''
                if cust:  # 给分享人（存在）则计数邀请数量
                    participates = XLInviteCode.objects.filter(mobile=cust.mobile)
                    if participates.exists():
                        participate = participates[0]
                        participate.usage_count += 1
                        participate.save()  # 使用次数累加
            return render_to_response(self.xlsampleapply,
                                      {"vipcode": vipcode, "pro": pro,
                                       "mobile": vmobile, "download": True},
                                      context_instance=RequestContext(request))

        return render_to_response(self.xlsampleapply,
                                  {"vipcode": vipcode, "pro": pro,
                                   "mobile": vmobile,
                                   "mobile_message": self.mobile_error_message},
                                  context_instance=RequestContext(request))


class APPDownloadView(View):
    """ 下载页面 """
    download_page = 'promotion/download.html'
    QQ_YINYONGBAO_URL = 'http://a.app.qq.com/o/simple.jsp?pkgname=com.jimei.xiaolumeimei'  # 腾讯应用宝下载跳转链接

    def get(self, request):
        content = request.REQUEST
        vipcode = content.get("vipcode", None)  # 活动邀请码
        from_customer = content.get("from_customer", None)  # 分享人的用户id
        url = '/sale/promotion/appdownload/?vipcode={0}&from_customer={1}'.format(vipcode, from_customer)
        agent = request.META.get('HTTP_USER_AGENT', None)  # 获取浏览器类型
        if "MicroMessenger" and 'iPhone' in agent:  # 如果是微信并且是iphone则跳转到应用宝下载
            url = self.QQ_YINYONGBAO_URL
            return redirect(url)
        return render_to_response(self.download_page,
                                  {"vipcode": vipcode, "from_customer": from_customer},
                                  context_instance=RequestContext(request))


class XlSampleOrderView(View):
    """
    免费申请试用活动，生成正式订单页面
    """
    order_page = 'promotion/xlsampleorder.html'
    share_link = 'sale/promotion/xlsampleapply/?from_customer={customer_id}'
    PROMOTION_LINKID_PATH = 'pmt'
    PROMOTE_CONDITION = 20

    def get_promotion_result(self, customer_id, outer_id, mobile):
        """ 返回自己的用户id　　返回邀请结果　推荐数量　和下载数量 """
        applys = XLSampleApply.objects.filter(from_customer=customer_id)
        promote_count = applys.count()  # 邀请的数量
        # 是否可以购买睡袋　邀请数量达到要求即可以跳转购买睡袋
        is_get_order = True if promote_count >= self.PROMOTE_CONDITION else False
        xlcodes = XLInviteCode.objects.filter(mobile=mobile)
        vipcode = None
        if xlcodes.exists():
            vipcode = xlcodes[0].vipcode
        # 下载appd 的数量(激活的数量)
        app_down_count = XLSampleOrder.objects.filter(xlsp_apply__in=applys.values('id')).count()
        download_str = str('%02.f' % app_down_count)
        inactive_count = applys.filter(status=XLSampleApply.INACTIVE).count()
        share_link = self.share_link.format(**{'customer_id': customer_id})
        # 用户活动红包
        reds = self.my_red_packets(customer_id)
        res = {'promote_count': promote_count, 'fist_num': download_str[0], "reds": reds,
               'second_num': download_str[1], "inactive_count": inactive_count,
               'share_link': share_link, 'link_qrcode': '', "vipcode": vipcode, 'is_get_order': is_get_order}
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
                XLSampleOrder.objects.create(xlsp_apply=new_xlapply.id, customer_id=customer.id,
                                             outer_id=outer_id, sku_code=sku_code)
                res = self.get_promotion_result(customer.id, outer_id, mobile)

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
        refreal_from = str(refreal_from)
        # 计算推荐人的下载激活数量
        applys = XLSampleApply.objects.filter(from_customer=refreal_from)  # 推荐人的邀请记录
        app_down_count = XLSampleOrder.objects.filter(xlsp_apply__in=applys.values('id')).count()  # 推荐人的激活记录
        ReadPacket.objects.release133_packet(refreal_from, app_down_count)

    def my_red_packets(self, customer):
        """
        用户活动红包
        """
        reds = ReadPacket.objects.filter(customer=customer)
        return reds

    def get(self, request):
        title = "元宵好兆头 抢红包 赢睡袋"
        pro = get_active_pros_data()  # 获取活动产品数据

        # 如果用户已经有正式订单存在 则 直接返回分享页
        customer = get_customer(request)
        if customer:
            outer_id = pro.outer_id
            xls_orders = XLSampleOrder.objects.filter(customer_id=customer.id).order_by('-created')
            if xls_orders.exists():
                customer_id = customer.id
                mobile = customer.mobile
                res = self.get_promotion_result(customer_id, outer_id, mobile)
                return render_to_response(self.order_page, {'pro': pro, 'res': res},
                                          context_instance=RequestContext(request))
        return render_to_response(self.order_page, {"pro": pro, "title": title},
                                  context_instance=RequestContext(request))

    def post(self, request):
        content = request.REQUEST
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
        xlapplys = XLSampleApply.objects.filter(mobile=mobile, outer_id=outer_id).order_by('-created')
        xlapply = None

        if xlapplys.exists():
            xlapply = xlapplys[0]

        # 获取自己的正式使用订单
        xls_orders = XLSampleOrder.objects.filter(customer_id=customer.id, outer_id=outer_id).order_by('-created')

        if not xls_orders.exists():  # 没有　试用订单　创建　正式　订单记录
            if xlapply:  # 有　试用申请　记录的
                XLSampleOrder.objects.create(xlsp_apply=xlapply.id, customer_id=customer.id,
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
                self.release_packet_for_refreal(referal_uid)

            else:  # 没有试用申请记录的（返回申请页面链接）　提示
                not_apply_message = "您还没有申请记录,请填写邀请码"
                if vipcode not in (None, ""):  # 有邀请码的情况下 根据邀请码生成用户的申请记录和订单记录
                    res = self.handler_with_vipcode(vipcode, mobile, outer_id, sku_code, customer)
                    if res is not None:
                        return render_to_response(self.order_page, {"res": res},
                                                  context_instance=RequestContext(request))
                    else:
                        not_apply_message = "您的邀请码有误，尝试重新填写"
                return render_to_response(self.order_page, {"pro": pro,
                                                            "title": title,
                                                            "not_apply": not_apply_message},
                                          context_instance=RequestContext(request))
        outer_ids = ['', ]
        outer_ids[0] = outer_id
        res = self.get_promotion_result(customer.id, outer_ids, mobile)
        return render_to_response(self.order_page, {"pro": pro, "res": res}, context_instance=RequestContext(request))


def get_customer(request):
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        customer = None
    return customer


class CusApplyOrdersView(APIView):
    """
     获取用户的推荐申请　和　激活　信息
    """
    promote_condition = 'promotion/friendlist.html'

    def get(self, request):
        customer = get_customer(request)
        customer_id = customer.id if customer else 0

        applys = XLSampleApply.objects.filter(from_customer=customer_id)
        # 计算当前用户的邀请情况　和　激活情况
        inactives = []
        inactive_applys = applys.filter(status=XLSampleApply.INACTIVE)  # 没有激活情况
        for inactive in inactive_applys:
            mobile = inactive.mobile
            condition = {"mobile": mobile, "thumbnail": ''}
            inactives.append(condition)
        # 返回邀请关系表中是自己邀请的用户的头像和手机号码

        ships = XLReferalRelationship.objects.filter(referal_from_uid=customer_id)
        referal_uids = ships.values('referal_uid')
        referals_sus = Customer.objects.filter(id__in=referal_uids)
        condition = {"referals_sus": referals_sus, 'inactives': inactives}

        return render_to_response(self.promote_condition, condition,
                                  context_instance=RequestContext(request))


def get_mobile_show(customer):
    mobile = ''.join([customer.mobile[0:3], "****", customer.mobile[7:11]])
    thumbnail = customer.thumbnail or 'http://7xogkj.com2.z0.glb.qiniucdn.com/Icon-60%402x.png'  # 小鹿logo缺省头像
    applys = XLSampleApply.objects.filter(from_customer=customer.id, outer_id='90061232563')
    promote_count = applys.count()  # 邀请的数量　
    app_down_count = XLSampleOrder.objects.filter(xlsp_apply__in=applys.values('id')).count()  # 下载appd 的数量

    res = (mobile, promote_count, app_down_count, thumbnail)
    return res


def get_orders(month=None, batch=None):
    order_list = XLSampleOrder.objects.none()
    if month == 1602 and batch == 1:
        start_time = datetime.datetime(2016, 1, 22)
        order_list = XLSampleOrder.objects.filter(created__gt=start_time)
    if not (month and batch):
        start_time = datetime.datetime(2016, 1, 22)
        orders = XLSampleOrder.objects.filter(created__gt=start_time)
        order_list = orders[:30] if len(orders) > 30 else orders  # 只是取30条
    return order_list


class PromotionShortResult(APIView):
    def get(self, request):
        items = []
        order_list = get_orders(None, None)
        customer_ids = [item.customer_id for item in order_list]
        wx_users = Customer.objects.filter(id__in=customer_ids)
        for user in wx_users:
            items.append(get_mobile_show(user))
        return HttpResponse(json.dumps(items))


class PromotionResult(APIView):
    """
    活动中奖结果展示
    """
    result_page = 'promotion/pmt_result.html'
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (BrowsableAPIRenderer,)

    def get(self, request, *args, **kwargs):
        page = int(kwargs.get('page', 1))
        batch = int(kwargs.get('batch', 1))
        month = int(kwargs.get('month', 1))
        order_list = get_orders(month=month, batch=batch)
        num_per_page = 20  # Show 20 contacts per page
        paginator = Paginator(order_list, num_per_page)

        try:
            items = paginator.page(page)
        except PageNotAnInteger:  # If page is not an integer, deliver first page.
            items = paginator.page(1)
        except EmptyPage:  # If page is out of range (e.g. 9999), deliver last page of results.
            items = paginator.page(paginator.num_pages)

        customer_ids = [item.customer_id for item in items]
        wx_users = Customer.objects.filter(id__in=customer_ids)
        items = []
        for user in wx_users:
            items.append(get_mobile_show(user))

        total = order_list.count()  # 总条数
        num_pages = paginator.num_pages  # 当前页

        next_page = min(page + 1, num_pages)
        prev_page = max(page - 1, 1)
        res = {"items": items, 'num_pages': num_pages,
               'total': total, 'num_per_page': num_per_page,
               'prev_page': prev_page, 'next_page': next_page,
               'page': page, 'batch': batch, 'month': month}
        response = render_to_response(self.result_page, res, context_instance=RequestContext(request))
        return response

