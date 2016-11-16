# coding=utf-8


import json
import time
from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.db.models import Sum

from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.response import Response

from core.weixin.mixins import WeixinAuthMixin
from flashsale.coupon.models import UserCoupon
from flashsale.pay.models import Customer
from flashsale.promotion.models import ActivityEntry

from shopback.items.models import Product
from shopapp.weixin.options import get_openid_by_unionid

from flashsale.promotion.models import XLSampleApply, XLSampleOrder, RedEnvelope, AwardWinner
from ..serializers.envelope import RedEnvelopeSerializer
from ..serializers.awardwinner import AwardWinnerSerializer
from flashsale.promotion.utils import get_application

import logging

logger = logging.getLogger(__name__)


def get_customer(request):
    user = request.user
    if not user or user.is_anonymous():
        return None
    try:
        customer = Customer.objects.get(user_id=request.user.id)
    except Customer.DoesNotExist:
        customer = None
    return customer


def get_activity_entry(event_id):
    activity_entrys = ActivityEntry.objects.filter(id=event_id)
    if activity_entrys.count() > 0:
        return activity_entrys[0]
    return None


class ActivityView(WeixinAuthMixin, APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    # permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)
    template_name = "promotion/discount_activity.html"

    def get_product_list(self):
        products = []
        if settings.DEBUG:
            pids = (1, 2, 3, 4, 5)
        else:
            pids = (36451, 36443, 36249, 36449, 36457)
        for pid in pids:
            product = Product.objects.get(id=pid)
            products.append(product)
        return products

    def get(self, request, *args, **kwargs):

        product_list = self.get_product_list()
        return Response({'product_list': product_list})


class JoinView(WeixinAuthMixin, APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    renderer_classes = (renderers.JSONRenderer,)

    def get(self, request, event_id, *args, **kwargs):
        content = request.GET
        ufrom = content.get("ufrom", "")
        from_customer = content.get("from_customer", "")
        mama_id = content.get("mama_id", "")

        # the following is for debug
        # if ufrom == 'app':
        #    response = redirect(reverse('app_join_activity', args=(event_id,)))
        # else:
        #    response = redirect(reverse('web_join_activity', args=(event_id,)))

        # this is for production
        if self.is_from_weixin(request):
            response = redirect(reverse('weixin_baseauth_join_activity', args=(event_id,)))
        elif ufrom == "app":
            response = redirect(reverse('app_join_activity', args=(event_id,)))
        else:
            response = redirect(reverse('web_join_activity', args=(event_id,)))

        response.set_cookie("mm_linkid", mama_id)
        response.set_cookie("event_id", event_id)
        response.set_cookie("from_customer", from_customer)
        response.set_cookie("ufrom", ufrom)
        return response


class WeixinBaseAuthJoinView(WeixinAuthMixin, APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    renderer_classes = (renderers.JSONRenderer,)

    def get(self, request, event_id, *args, **kwargs):
        # 1. check whether event_id is valid
        self.set_appid_and_secret(settings.WXPAY_APPID, settings.WXPAY_SECRET)
        activity_entry = get_activity_entry(event_id)
        if not activity_entry:
            return Response({"error": "wrong event id"})

            # 2. get openid from cookie
        openid, unionid = self.get_cookie_openid_and_unoinid(request)

        if not self.valid_openid(openid):
            # 3. get openid from 'debug' or from using 'code' (if code exists)
            userinfo = self.get_auth_userinfo(request)
            openid = userinfo.get("openid")

            if not self.valid_openid(openid):
                # 4. if we still dont have openid, we have to do oauth
                redirect_url = self.get_wxauth_redirct_url(request)
                return redirect(redirect_url)
                # logger.warn("baseauth: %s" % userinfo)

        # now we already have openid, we check whether application exists.
        application_count = XLSampleApply.objects.filter(user_openid=openid, event_id=event_id).count()
        if application_count <= 0:
            key = 'apply'
        else:
            key = 'download'

        html = activity_entry.get_html(key)
        response = redirect(html)

        if key == 'apply':
            self.set_cookie_openid_and_unionid(response, openid, unionid)

        return response


class WeixinSNSAuthJoinView(WeixinAuthMixin, APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    renderer_classes = (renderers.JSONRenderer,)

    def get(self, request, event_id, *args, **kwargs):
        # 1. check whether event_id is valid
        self.set_appid_and_secret(settings.WXPAY_APPID, settings.WXPAY_SECRET)
        activity_entry = get_activity_entry(event_id)
        if not activity_entry:
            return Response({"error": "wrong event id"})

            # 2. get openid from cookie
        openid, unionid = self.get_cookie_openid_and_unoinid(request)

        if not self.valid_openid(unionid):
            # 3. get openid from 'debug' or from using 'code' (if code exists)
            userinfo = self.get_auth_userinfo(request)
            unionid = userinfo.get("unionid")
            openid = userinfo.get("openid")

            if not self.valid_openid(unionid):
                # 4. if we still dont have openid, we have to do oauth
                redirect_url = self.get_snsuserinfo_redirct_url(request)
                return redirect(redirect_url)

            # now we have userinfo
            # logger.warn("snsauth: %s" % userinfo)
            from .tasks_activity import task_userinfo_update_application
            task_userinfo_update_application.delay(userinfo)

        # now we already have openid, we check whether application exists.
        application_count = XLSampleApply.objects.filter(user_openid=openid, event_id=event_id).count()
        if application_count <= 0:
            key = 'apply'
        else:
            key = 'download'

        html = activity_entry.get_html(key)
        response = redirect(html)
        self.set_cookie_openid_and_unionid(response, openid, unionid)

        return response


class AppJoinView(WeixinAuthMixin, APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer,)

    def get(self, request, event_id, *args, **kwargs):
        # 1. check whether event_id is valid
        activity_entry = get_activity_entry(event_id)
        if not activity_entry:
            return Response({"error": "wrong event id"})

        customer = get_customer(request)
        if not customer or not customer.mobile:
            return Response({"bind": False})

        unionid = customer.unionid
        openid = get_openid_by_unionid(unionid, settings.WXPAY_APPID)

        application = get_application(event_id, unionid, customer.mobile)
        if not application:
            key = 'apply'
        else:
            key = 'activate'

        # logger.warn("AppJoinView: customer=%s, event_id=%s, key=%s, openid=%s" % (customer.nick, event_id, key, openid))

        html = activity_entry.get_html(key)
        response = redirect(html)
        self.set_cookie_openid_and_unionid(response, openid, unionid)

        return response


class WebJoinView(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    renderer_classes = (renderers.JSONRenderer,)

    def get(self, request, event_id, *args, **kwargs):
        # 1. check whether event_id is valid
        activity_entry = get_activity_entry(event_id)
        if not activity_entry:
            return Response({"error": "wrong event id"})

            # 2. get mobile from cookie
        mobile = request.COOKIES.get("mobile", "")

        key = 'apply'
        if mobile:
            application_count = XLSampleApply.objects.filter(mobile=mobile, event_id=event_id).count()
            if application_count > 0:
                key = 'download'

        # logger.warn("WebJoinView: event_id=%s, key=%s" % (event_id, key))

        html = activity_entry.get_html(key)
        return redirect(html)


class ApplicationView(WeixinAuthMixin, APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    # permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer,)

    def get(self, request, event_id, *args, **kwargs):
        content = request.GET
        from_customer = request.COOKIES.get("from_customer", "")
        mobile = request.COOKIES.get("mobile")
        imei = content.get('mobileSNCode') or ''  # 用户设备号
        openid, unionid = self.get_cookie_openid_and_unoinid(request)

        # 1. check whether event_id is valid
        activity_entry = get_activity_entry(event_id)
        if not activity_entry:
            return Response({"rcode": 1, "msg": "wrong event id"})

        customer = get_customer(request)
        if customer:
            openid = get_openid_by_unionid(customer.unionid, settings.WXPAY_APPID)
            mobile = customer.mobile

        applied = False
        application_count = 0
        if openid:
            applications = XLSampleApply.objects.filter(user_openid=openid, event_id=event_id)
            application_count = applications.count()
        elif mobile:
            applications = XLSampleApply.objects.filter(mobile=mobile, event_id=event_id)
            application_count = applications.count()
        if application_count > 0:
            try:
                application = applications[0]
                if imei:
                    application.event_imei = '{0}_{1}'.format(event_id, imei)
                    application.save()
            except Exception, exc:
                logger.warn(exc.message)
            applied = True

        mobile_required = True
        if mobile or self.valid_openid(openid):
            mobile_required = False

        img, nick = "http://7xogkj.com2.z0.glb.qiniucdn.com/222-ohmydeer.png?imageMogr2/thumbnail/100/format/png", u"小鹿妈妈"
        if from_customer:
            try:
                customer = Customer.objects.get(id=from_customer)
                if customer.thumbnail:
                    img = customer.thumbnail
                if customer.nick:
                    nick = customer.nick
            except Customer.DoesNotExist:
                pass

        end_time = int(time.mktime(activity_entry.end_time.timetuple()) * 1000)
        # logger.warn("ApplicationView GET: end_time=%s, mobile_required:%s, openid:%s, mobile:%s, customer:%s" % (
        # end_time, mobile_required, openid, mobile, customer))

        res_data = {"applied": applied, "img": img, "nick": nick, "end_time": end_time,
                    "mobile_required": mobile_required}
        response = Response(res_data)
        response.set_cookie("mobile", mobile)
        self.set_cookie_openid_and_unionid(response, openid, unionid)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    def post(self, request, event_id, *args, **kwargs):
        content = request.POST
        ufrom = request.COOKIES.get("ufrom", None)
        mobile = content.get("mobile", None)
        imei = content.get('mobileSNCode') or ''  # 用户设备号
        from_customer = request.COOKIES.get("from_customer", None)

        openid, unionid = self.get_cookie_openid_and_unoinid(request)

        # if mobile is not provided as parameter, get mobile from cookie.
        if not mobile:
            mobile = request.COOKIES.get("mobile", None)

        if not (mobile or self.valid_openid(openid)):
            response = Response({"rcode": 1, "msg": "openid or moible must be provided one"})
            response["Access-Control-Allow-Origin"] = "*"
            return response

        application_count = 0
        if unionid:
            applications = XLSampleApply.objects.filter(user_unionid=unionid, event_id=event_id)
            application_count = applications.count()
        elif openid:
            applications = XLSampleApply.objects.filter(user_openid=openid, event_id=event_id)
            application_count = applications.count()
        elif mobile:
            from flashsale.restpro.v2.views_verifycode_login import validate_mobile
            if not validate_mobile(mobile):
                response = Response({"rcode": 2, "msg": "mobile number wrong"})
                response["Access-Control-Allow-Origin"] = "*"
                return response
            applications = XLSampleApply.objects.filter(mobile=mobile, event_id=event_id)
            application_count = applications.count()
        if application_count > 0:
            # 保存设备号
            try:
                application = applications[0]
                if imei:
                    application.event_imei = '{0}_{1}'.format(event_id, imei)
                    application.save()
            except Exception, exc:
                logger.warn(exc.message)
        params = {}
        customer = get_customer(request)
        if from_customer:
            params.update({"from_customer": from_customer})
        if ufrom:
            params.update({"ufrom": ufrom})
        if unionid:
            params.update({"user_unionid": unionid})
        if openid:
            params.update({"user_openid": openid})
        if mobile:
            params.update({"mobile": mobile})
        if customer and ufrom == "app":
            params.update({"customer_id": customer.id, "status": XLSampleApply.ACTIVED})

        if application_count <= 0:
            # logger.warn("ApplicationView post: application_count=%s, create sampleapply record" % application_count)
            application = XLSampleApply(event_id=event_id, **params)
            application.save()

        next_page = "download"
        if self.is_from_weixin(request):
            next_page = "snsauth"
        if ufrom == "app":
            next_page = "activate"

        response = Response({"rcode": 0, "msg": "application submitted", "next": next_page})
        response.set_cookie("mobile", mobile)
        response["Access-Control-Allow-Origin"] = "*"
        return response


class ActivateView(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer,)

    def get(self, request, event_id, *args, **kwargs):
        # 1. check whether event_id is valid
        content = request.GET
        imei = content.get('mobileSNCode') or ''  # 用户设备号
        activity_entry = get_activity_entry(event_id)
        if not activity_entry:
            return Response({"error": "wrong event id"})

            # 2. activate application
        customer = get_customer(request)
        from tasks_activity import task_activate_application
        task_activate_application.delay(event_id, customer, imei)

        # 3. redirect to mainpage
        key = 'mainpage'
        html = activity_entry.get_html(key)
        response = redirect(html)
        response["Access-Control-Allow-Origin"] = "*"
        return response


class MainView(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer,)

    def get(self, request, event_id, *args, **kwargs):
        customer = get_customer(request)
        customer_id = customer.id
        # customer_id = 1 # debug
        envelopes = RedEnvelope.objects.filter(event_id=event_id, customer_id=customer_id)

        winner_count = AwardWinner.objects.filter(event_id=event_id).count()
        award_left = 2000 - winner_count
        latest_five = AwardWinner.objects.filter(event_id=event_id).order_by('-created')[:5]

        envelope_serializer = RedEnvelopeSerializer(envelopes, many=True)
        winner_serializer = AwardWinnerSerializer(latest_five, many=True)

        # cards = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
        cards = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        num_cards = 0
        for item in envelope_serializer.data:
            if item['type'] == 'card' and item['status'] == 'open':
                index = item['value']
                cards[index - 1] = 1
                num_cards += 1

        inactive_applications = XLSampleApply.objects.filter(event_id=event_id, from_customer=customer_id,
                                                             status=XLSampleApply.INACTIVE).order_by('-created')
        envelopes = envelope_serializer.data
        num_of_envelope = len(envelopes)
        for item in inactive_applications:
            envelopes.append({"headimgurl": item.headimgurl, "nick": item.nick, "type": "inactive"})

        # cards,num_cards = [1, 1, 1, 1, 1, 1, 1, 1, 1],9

        data = {"cards": cards, "envelopes": envelopes, "num_of_envelope": num_of_envelope,
                "award_list": winner_serializer.data, "award_left": award_left, "num_cards": num_cards}

        response = Response(data)
        response["Access-Control-Allow-Origin"] = "*"
        return response


class OpenEnvelopeView(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer,)

    def get(self, request, envelope_id, *args, **kwargs):
        # 1. we have to check login
        content = request.GET

        customer = Customer.objects.get(user=request.user)
        customer_id = customer.id

        if envelope_id <= 0:
            return Response({"rcode": 1, "msg": "envelope id wrong"})
        envelopes = RedEnvelope.objects.filter(id=envelope_id)
        if envelopes.count() <= 0:
            return Response({"msg": "open failed, no envelope found"})

        envelope = envelopes[0]
        if envelope.status == 0:
            envelope.status = 1  # otherwise, return envelope.status is 0.
            envelope.save()

        event_id = envelope.event_id
        serializer = RedEnvelopeSerializer(envelope)

        num_cards = RedEnvelope.objects.filter(event_id=event_id, customer_id=customer_id, type=1, status=1).count()

        data = serializer.data
        data.update({"num_cards": num_cards})

        response = Response(data)
        response["Access-Control-Allow-Origin"] = "*"
        return response


class StatsView(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer,)

    def get(self, request, event_id, *args, **kwargs):
        customer = Customer.objects.get(user=request.user)
        customer_id = customer.id
        # customer_id = 1  # debug
        envelopes = RedEnvelope.objects.filter(customer_id=customer_id, event_id=event_id)
        invite_num = envelopes.count()

        res = envelopes.filter(type=0).values('type').annotate(total=Sum('value'))
        total = 0
        if res:
            total = float("%.2f" % (res[0]["total"] * 0.01))

        envelope_serializer = RedEnvelopeSerializer(envelopes, many=True)
        cards = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        for item in envelope_serializer.data:
            if item['type'] == 'card' and item['status'] == 'open':
                index = item['value']
                cards[index - 1] = 1

        try:
            winner = AwardWinner.objects.get(customer_id=customer_id)
            if winner:
                status = winner.status
            else:
                status = 0
        except AwardWinner.DoesNotExist:
            status = 0

        response = Response({"invite_num": invite_num, "total": total, "cards": cards, "status": status})
        response["Access-Control-Allow-Origin"] = "*"
        return response


class GetAwardView(APIView):
    ''' 达到赢取奖品条件后,获得奖品 '''
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer,)

    def post(self, request, event_id, *args, **kwargs):
        content = request.POST
        template_id = content.get("template_id", None)

        customer = Customer.objects.get(user=request.user)
        customer_id = customer.id
        buyer_id = str(customer_id)

        # coups = UserCoupon.objects.filter(customer=buyer_id, cp_id__template__id=template_id)
        code, msg = 0, ""
        # if coups.count() <= 0:
        cou, code, msg = UserCoupon.objects.create_normal_coupon(buyer_id=customer, template_id=template_id)

        if code == 0:
            winner = AwardWinner.objects.get(customer_id=customer_id, event_id=event_id)
            winner.status = 1
            winner.save()

        response = Response({"code": code, "res": msg})
        response["Access-Control-Allow-Origin"] = "*"
        return response
