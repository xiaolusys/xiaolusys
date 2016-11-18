# coding=utf-8
import os
import re
import collections
import datetime
import decimal
import urlparse

from django.conf import settings
from django.db.models import Sum, Count
from django.forms import model_to_dict
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.exceptions import APIException
from flashsale.restpro import permissions as perms
from rest_framework.response import Response
from core.options import log_action, ADDITION, CHANGE
from flashsale.clickcount.models import ClickCount
from flashsale.clickcount.models import Clicks
from flashsale.clickrebeta.models import StatisticsShopping
from flashsale.coupon.models import UserCoupon, CouponTemplate
from flashsale.pay.mixins import PayInfoMethodMixin
from flashsale.pay.models import BudgetLog
from flashsale.pay.models import Customer
from flashsale.pay.models import SaleTrade
from flashsale.xiaolumm.models import XiaoluMama, CarryLog, CashOut, PotentialMama, ReferalRelationship
from flashsale.xiaolumm.models.models_fans import XlmmFans, FansNumberRecord
from flashsale.xiaolumm.models.models_fortune import MamaFortune
from flashsale.pay.models import Envelop
from shopapp.weixin.models import WeixinUnionID


from shopback.items.models import Product, ProductSku
from . import serializers

import logging

logger = logging.getLogger(__name__)

from core.utils.regex import REGEX_MOBILE

PHONE_NUM_RE = re.compile(REGEX_MOBILE, re.IGNORECASE)


def validate_mobile(mobile):
    """
    check mobile format
    """
    if re.match(PHONE_NUM_RE, mobile):  # 进行正则判断
        return True
    return False


def get_mamafortune(mama_id):
    """　获取可提现金额 活跃值 """
    try:
        fortune = MamaFortune.objects.get(mama_id=mama_id)
        could_cash_out = fortune.cash_num_display()
        active_value_num = fortune.active_value_num
    except Exception, exc:
        raise APIException(u'{0}'.format(exc.message))
    return could_cash_out, active_value_num


class XiaoluMamaViewSet(viewsets.ModelViewSet, PayInfoMethodMixin):
    """
    ### 特卖平台－小鹿妈妈代理API:
    - {prefix}[.format] method:get : 获取登陆用户的代理基本信息
    - {prefix}/list_base_data　method:get : 获取代理推荐人信息
    - {prefix}/agency_info　method:get : 代理整理数据
    `recommend_num`: 总推荐数量
    `clk_num`: 今日点击
    `shop_num`: 今日订单
    `mobile`: 手机号
    `all_shop_num`: 所有订单数
    `mco`: 确定支出
    `ymco`: 昨日确定支出
    `pdc`: 总待确定金额
    `ymci`:昨日确定收入
    `mci`: 确定收入
    `cash`: 账户现金
    `mama_link`: 专属链接
    - [/rest/v1/pmt/xlmm/1461/new_mama_task_info](/rest/v1/pmt/xlmm/1461/new_mama_task_info)　代理id为1461的新手任务信息：
        1.  method: get
        3.  error return (HTTP 500 Internal Server Error):
            * {
                "detail": "妈妈未找到"
            }
            * {
                "detail": "参数错误"
            }
    """
    queryset = XiaoluMama.objects.all()
    serializer_class = serializers.XiaoluMamaSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.AllowAny, )
    # permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    MM_LINKID_PATH = 'qrcode/xiaolumm'

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        return self.queryset.filter(openid=customer.unionid)  # 通过customer的unionid找 xlmm

    def list(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated():
            raise exceptions.PermissionDenied()
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response()

    @detail_route(methods=['get'])
    def base_info(self, request, pk):
        try:
            pk = int(pk)
        except:
            raise exceptions.ValidationError(u'需要提供正确的小鹿妈妈ID')
        mama = get_object_or_404(XiaoluMama, pk=pk)
        if not mama:
            raise exceptions.ValidationError(u'此用户并非小鹿妈妈')
        res = {
            'mama_id': mama.id,
            'nick': mama.get_customer().nick,
            'thumbnail': mama.get_customer().thumbnail
        }
        return Response(res)

    @list_route(methods=['get'])
    def list_base_data(self, request):
        """
        该代理推荐的人
        """
        if not request.user or not request.user.is_authenticated():
            raise exceptions.PermissionDenied()
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm
        qst = self.queryset.filter(referal_from=xlmm.mobile)
        serializer = self.get_serializer(qst, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def agency_info(self, request):
        """ wap 版本页面数据整理显示　"""
        if not request.user or not request.user.is_authenticated():
            raise exceptions.PermissionDenied()
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm

        recommend_num = self.queryset.filter(referal_from=xlmm.mobile).count()  # 总推荐数量
        cash = xlmm.cash_money  # 账户现金
        carry_logs = CarryLog.objects.filter(xlmm=xlmm.id).exclude(status=CarryLog.CANCELED)  # 该代理的收支记录
        today = datetime.date.today()
        yestoday = today - datetime.timedelta(days=1)
        cfm_in = carry_logs.filter(carry_type=CarryLog.CARRY_IN, status=CarryLog.CONFIRMED)
        cfm_out = carry_logs.filter(carry_type=CarryLog.CARRY_OUT, status=CarryLog.CONFIRMED)
        yst_cfm_in = carry_logs.filter(carry_type=CarryLog.CARRY_IN, status=CarryLog.CONFIRMED, carry_date=yestoday)
        yst_cfm_out = carry_logs.filter(carry_type=CarryLog.CARRY_OUT, status=CarryLog.CONFIRMED, carry_date=yestoday)
        pending = carry_logs.filter(status=CarryLog.PENDING)
        nmc_in = carry_logs.filter(carry_type=CarryLog.CARRY_IN, status__in=(CarryLog.CONFIRMED, CarryLog.PENDING),
                                   carry_date=today)
        nmc_clk = carry_logs.filter(status__in=(CarryLog.CONFIRMED, CarryLog.PENDING), log_type=CarryLog.CLICK_REBETA)

        mci = (cfm_in.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0  # 确定收入
        mco = (cfm_out.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0  # 确定支出
        ymci = (yst_cfm_in.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0  # 昨日确定收入
        ymco = (yst_cfm_out.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0  # 昨日确定支出
        pdc = (pending.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0  # 总待确定金额
        nmci = (nmc_in.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0  # 今日收入(含待收入)
        clki = (nmc_clk.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0  # 历史点击收入(含待收入)
        mmclog = {"mci": mci, "mco": mco, "ymci": ymci, "ymco": ymco, "pdc": pdc, "nmci": nmci, 'clki': clki}

        # 今日有效点击数量
        clks = ClickCount.objects.filter(linkid=xlmm.id, date=today)
        clk_num = clks.aggregate(clk_num=Sum('valid_num')).get('clk_num') or 0
        # 今日订单
        t_from = datetime.datetime(today.year, today.month, today.day, 0, 0, 0)
        t_to = datetime.datetime(today.year, today.month, today.day, 23, 59, 59)
        all_shops = StatisticsShopping.objects.filter(linkid=xlmm.id, status__in=(StatisticsShopping.FINISHED,
                                                                                  StatisticsShopping.WAIT_SEND))
        all_shop_num = all_shops.count()
        shop_num = all_shops.filter(shoptime__gte=t_from, shoptime__lte=t_to).count()  # 今日订单数量

        # 计算今日点击金额
        clk_money = xlmm.get_Mama_Click_Price(shop_num) * clk_num

        mama_link = os.path.join(settings.M_SITE_URL, "m/{}/".format(xlmm.id))  # 专属链接
        # share_mmcode = xlmm.get_share_qrcode_path()  20160406 wulei 此字段转换为存储妈妈邀请新代理的h5页面url
        from flashsale.restpro import constants

        share_mmcode = constants.MAMA_INVITE_AGENTCY_URL.format(**{'site_url': settings.M_SITE_URL})

        share_qrcode = xlmm.get_share_qrcode_url()
        # 代理的粉丝数量
        fans = FansNumberRecord.objects.filter(xlmm_cusid=customer.id)
        fans_num = fans[0].fans_num if fans.exists() else 0

        data = {"xlmm": xlmm.id, "mobile": xlmm.mobile,
                "recommend_num": recommend_num, "cash": cash,
                "mmclog": mmclog, "clk_num": clk_num,
                "mama_link": mama_link, "shop_num": shop_num,
                "all_shop_num": all_shop_num,
                "share_mmcode": share_mmcode, 'share_qrcode': share_qrcode,
                "clk_money": clk_money, "fans_num": fans_num}
        return Response(data)

    @list_route(methods=['get'])
    def get_fans_list(self, request):
        """ 获取小鹿妈妈的粉丝列表 """
        if not request.user or not request.user.is_authenticated():
            raise exceptions.PermissionDenied()
        customer = get_object_or_404(Customer, user=request.user)
        xlmm_fans = XlmmFans.objects.filter(xlmm_cusid=customer.id).order_by('created')
        page = self.paginate_queryset(xlmm_fans)
        if page is not None:
            fans_cusids = [p.fans_cusid for p in page]
            customers = Customer.objects.normal_customer.filter(id__in=fans_cusids)
            data = customers.values('id', 'nick', 'thumbnail')
            return self.get_paginated_response(data)

        fans_cusids = [cus[0] for cus in xlmm_fans.values('fans_cusid')]
        customers = Customer.objects.normal_customer.filter(id__in=fans_cusids)
        data = customers.values('id', 'nick', 'thumbnail')
        return Response(data)

    @list_route(methods=['get'])
    def get_referal_mama(self, request):
        """
        当前代理邀请的人数(正式，　非正式)　邀请人的信息（正式非正式）
        一元试用的从潜在用户列表中获取
        """
        if not request.user or not request.user.is_authenticated():
            raise exceptions.PermissionDenied()
        last_renew_type = request.GET.get("last_renew_type") or None
        if not last_renew_type:
            return Response([])
        currentmm = self.filter_queryset(self.get_owner_queryset(request)).first()
        if not currentmm:
            return Response([])
        if last_renew_type == 'trial':
            potential_mamas = PotentialMama.objects.filter(referal_mama=currentmm.id, is_full_member=False).order_by('-created')
            page = self.paginate_queryset(potential_mamas)
            serializer = serializers.PotentialInfoSerialize(page, many=True)
            if page is not None:
                return self.get_paginated_response(serializer.data)
            return Response(serializer.data)

        if last_renew_type == 'full':
            ships = ReferalRelationship.objects.filter(referal_from_mama_id=currentmm.id,referal_type__gte=XiaoluMama.HALF).order_by('-created')
            page = self.paginate_queryset(ships)
            serializer = serializers.RelationShipInfoSerialize(page, many=True)
            if page is not None:
                return self.get_paginated_response(serializer.data)
            return Response(serializer.data)

    def get_full_link(self, link):
        return urlparse.urljoin(settings.M_SITE_URL, link)

    def get_deposite_product(self):
        return Product.objects.get(id=2731)

    @list_route(methods=['get'])
    def get_register_pro_info(self, request):
        if not request.user or not request.user.is_authenticated():
            raise exceptions.PermissionDenied()
        content = request.GET
        # mama_id = content.get('mama_id', '1')
        # xlmm = self.get_xiaolumm(request)
        # register_url = "/m/register/?mama_id={0}".format(mama_id)
        # if not xlmm or xlmm.progress == XiaoluMama.NONE:  # 为申请或者没有填写资料跳转到邀请函页面
        # return redirect(register_url)
        #
        # if mama_id == xlmm.id or not xlmm.need_pay_deposite():
        # download_url = '/sale/promotion/appdownload/'
        # return redirect(download_url)

        product = self.get_deposite_product()
        serializer = serializers.DepositProductSerializer(product)
        skus = product.normal_skus
        deposite_params = [self.calc_deposite_amount_params(request, sku) for sku in skus]
        return Response({
            'uuid': self.get_trade_uuid(),
            'product': serializer.data,
            'payinfos': deposite_params,
            # 'referal_mamaid': mama_id,
            # 'success_url': self.get_full_link(reverse('mama_registerok')),
            # 'cancel_url': self.get_full_link(reverse('mama_registerfail') + '?mama_id=' + mama_id)
        })

    def bind_xlmm_info(self, xlmm, mobile, referal_from):
        if validate_mobile(mobile):
            xlmm.fill_info(mobile, referal_from)
        else:
            raise exceptions.APIException(u'手机号错误')
        return True

    @list_route(methods=['get', 'post'])
    def fill_mama_info(self, request):
        if not request.user or not request.user.is_authenticated():
            raise exceptions.PermissionDenied()
        content = request.data
        customer = get_object_or_404(Customer, user=request.user)
        mama_mobile = content.get('mama_mobile') or ''
        if (not customer.unionid) or (not customer.unionid.strip()):
            raise exceptions.APIException(u'没有授权微信登陆哦~')
        # if not mama_mobile:
        # raise exceptions.APIException(u'没有填写手机号哦~')
        xlmm = XiaoluMama.objects.filter(openid=customer.unionid).first()
        # if xlmm:
        # 如果是正式妈妈　并且购买的是试用产品 返回已经是正式妈妈  # 如果没有填写资料 返回需要填写资料
        # if xlmm.mobile is None or (not xlmm.mobile.strip()):
        # referal_from = ''  # referal_mama.mobile if referal_mama else ''
        # self.bind_xlmm_info(xlmm, mama_mobile, referal_from)
        if not xlmm:  # 创建小鹿妈妈
            if customer.unionid and customer.unionid.strip():
                xlmm = XiaoluMama(openid=customer.unionid)
                if validate_mobile(mama_mobile):
                    xlmm.mobile = mama_mobile
                xlmm.save()
            else:
                raise exceptions.APIException(u'注册妈妈出错啦~')
        serializer = self.get_serializer(xlmm)
        return Response(serializer.data)

    @list_route(methods=['get', 'post'])
    def mama_register_pay(self, request):
        if not request.user or not request.user.is_authenticated():
            raise exceptions.PermissionDenied()

        content = {}
        for k,v in request.POST.iteritems():
            content[k] = v

        product_id = content.get('product_id')
        sku_id = content.get('sku_id')
        sku_num = int(content.get('num', '1'))
        product = get_object_or_404(Product, id=product_id)
        product_sku = get_object_or_404(ProductSku, id=sku_id)
        payment = int(float(content.get('payment', '0')) * 100)
        post_fee = int(float(content.get('post_fee', '0')) * 100)
        discount_fee = int(float(content.get('discount_fee', '0')) * 100)
        bn_totalfee = int(product_sku.agent_price * sku_num * 100)
        wallet_renew_deposit = content.get('wallet_renew_deposit', 0)
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm

        logger.info({'action': 'v1_mama_register_pay', 'mama_id': xlmm.id})

        if float(wallet_renew_deposit) > 0:  # 续费押金
            could_cash_out, _ = get_mamafortune(xlmm.id)  # 可提现的金额(元)
            payment += could_cash_out * 100

        if product_sku.free_num < sku_num or product.shelf_status == Product.DOWN_SHELF:
            raise exceptions.ParseError(u'商品已被抢光啦！')

        bn_payment = bn_totalfee + post_fee - discount_fee
        if post_fee < 0 or payment <= 0 or abs(payment - bn_payment) > 10:
            raise exceptions.ParseError(u'付款金额异常')
        channel = content.get('channel')
        if channel not in dict(SaleTrade.CHANNEL_CHOICES):
            raise exceptions.ParseError(u'付款方式有误')

        try:
            lock_success = Product.objects.lockQuantity(product_sku, sku_num)
            if not lock_success:
                raise exceptions.APIException(u'商品库存不足')
            address = None
            sale_trade, state = self.create_deposite_trade(content, address, customer)
            if state:
                self.create_SaleOrder_By_Productsku(sale_trade, product, product_sku, sku_num)
        except exceptions.APIException, exc:
            logger.info({'action': 'v1_mama_register_pay_error', 'mama_id': xlmm.id, 'message': exc.message})
            raise exc
        except Exception, exc:
            logger.error(exc.message, exc_info=True)
            logger.info({'action': 'v1_mama_register_pay_error', 'mama_id': xlmm.id, 'message': exc.message})
            Product.objects.releaseLockQuantity(product_sku, sku_num)
            raise exceptions.APIException(u'订单生成异常')
        print 'debug:', content
        response_charge = self.pingpp_charge(sale_trade, **content)
        return Response(response_charge)

    @detail_route(methods=['get'])
    def new_mama_task_info(self, request, pk, *args, **kwargs):
        """
        :arg pk XiaoluMama instance id
        :return
        {
            'first_carry_record': False,
            'first_fans_record': False,
            'first_coupon_share': False,
            'first_mama_recommend': False,
            'first_commission',
            'tutorial_link': ''
        }
        """
        if not request.user or not request.user.is_authenticated():
            raise exceptions.PermissionDenied()
        from flashsale.xiaolumm.models import MamaVebViewConf
        from flashsale.coupon.models import OrderShareCoupon
        from flashsale.xiaolumm.models import XlmmFans, PotentialMama
        from flashsale.xiaolumm.models.models_fortune import CarryRecord, OrderCarry

        customer = get_object_or_404(Customer, user=request.user)
        xlmm = self.queryset.filter(openid=customer.unionid).first()
        if not xlmm:
            raise exceptions.APIException('妈妈未找到')
        if xlmm.id != int(pk):
            raise exceptions.APIException('参数错误')

        default_config = collections.defaultdict(page_pop=False)
        default_return = collections.defaultdict(config=default_config, data=[])

        carry_record = CarryRecord.objects.filter(mama_id=xlmm.id, carry_type=CarryRecord.CR_CLICK).exists()
        fans_record = XlmmFans.objects.filter(xlmm=xlmm.id).exists()
        coupon_share = OrderShareCoupon.objects.filter(share_customer=customer.id).exists()
        commission = OrderCarry.objects.filter(mama_id=xlmm.id).exists()
        mama_recommend = ReferalRelationship.objects.filter(referal_from_mama_id=xlmm.id).exists() or \
            PotentialMama.objects.filter(referal_mama=xlmm.id).exists()

        default_return['data'].append({'complete': carry_record, 'desc': u'获得第一笔收益', 'show': True})
        default_return['data'].append({'complete': fans_record, 'desc': u'发展第一个粉丝', 'show': True})
        default_return['data'].append({'complete': coupon_share, 'desc': u'分享第一个红包', 'show': True})
        default_return['data'].append({'complete': commission, 'desc': u'赚取第一笔佣金', 'show': True})
        default_return['data'].append({'complete': mama_recommend, 'desc': u'发展第一个代理', 'show': True})

        conf = MamaVebViewConf.objects.filter(version='new_guy_task').first()  # 新手任务配置后台记录
        extra = conf.extra

        if extra['mama_recommend_show'] == 0:  # 推荐妈妈不显示的时候则将
            mama_recommend = True  # 不显示则默认完成
            default_return['data'][4]['show'] = False

        all_complete_flag = [carry_record, fans_record, coupon_share, commission, mama_recommend]

        task_all_complete = True if False not in all_complete_flag else False
        if task_all_complete:  # 任务全部完成
            default_return.update({'config': {'page_pop': False}})
        return Response(default_return)

    @list_route(methods=['get'])
    def get_team_members(self, request):
        try:
            xlmm = request.user.customer.get_xiaolumm()
        except Exception, e:
            raise exceptions.ValidationError(u'用户不是小鹿妈妈或者未登录')
        from flashsale.xiaolumm.models.rank import WeekMamaCarryTotal, WEEK_RANK_REDIS
        res = []
        mm_ids = xlmm.get_team_member_ids()
        for mama in XiaoluMama.objects.filter(id__in=mm_ids):
            fortune = MamaFortune.get_by_mamaid(mama.id)
            item = {
                'mama': mama.id,
                'thumbnail': mama.thumbnail,
                'nick': mama.nick,
                'mobile': mama.mobile,
                'num': fortune.order_num,
                'rank': WEEK_RANK_REDIS.get_rank(WeekMamaCarryTotal, 'total', mama.id),
                'total': fortune.cash_total,
                'total_display': '%.2f' % fortune.cash_total,
            }
            res.append(item)
        return Response(res)

    @list_route(methods=['get'])
    def get_my_leader_mama_baseinfo(self, request):
        try:
            xlmm = request.user.customer.get_xiaolumm()
        except Exception, e:
            raise exceptions.ValidationError(u'用户不是小鹿妈妈或者未登录')

        res = []

        r = ReferalRelationship.objects.filter(referal_to_mama_id=xlmm.id).first()
        if r:
            if r.referal_from_mama_id:
                mama = XiaoluMama.objects.filter(id=r.referal_from_mama_id)
        if mama:
            item = {
                'mama': mama.id,
                'thumbnail': mama.thumbnail,
                'nick': mama.nick,
                'mobile': mama.mobile,
            }
        res.append(item)
        return Response(res)


class CarryLogViewSet(viewsets.ModelViewSet):
    """
    ## 特卖平台－小鹿妈妈收支记录API:
    - {prefix}[.format] : 获取登陆用户的收支记录信息
        - log_type:
            `rebeta`: 订单返利
            `buy`: 消费支出
            `click`:点击兑现
            `refund`:退款返现
            `reoff`:退款扣除
            `cashout`:钱包提现
            `deposit`:押金
            `thousand`:千元提成
            `subsidy`:代理补贴
            `recruit`:招募奖金
            `ordred`:订单红包
            `flush`:补差额
            `recharge`:充值
    - {prefix}/list_base_data　method:get : 账户基本信息页面显示
        - return :
        `mci`: 已经确认收入
        `mco`:　已经确认支出   　
        `ymci`:　昨天确认收入
        `ymco`: 昨天确认支出
        `pdc`: 待确认金额
    - {prefix}/get_carryinlog method: get : 获取用户自己的收入记录
    `type_count`: 点击或者订单条数　如果为0　为非点击或订单收入记录类型
    `xlmm`: 代理的专属链接
    `sum_value`: 收入金额
    `carry_date`: 业务时间
    `log_type`: 收入类型
    >`click`: 点击补贴　分享返现  返
    `rebeta`: 订单返利　订单佣金　佣
    `recruit`:招募奖金  招募奖金  奖
    `subsidy`:代理补贴  推荐提成　　提
    `thousand`:千元提成　　额外奖励　 奖
    `ordred`:订单红包 　红包奖励　　奖
    `fans_carry`: 粉丝购买提成 粉
    `group_bonus:` 团队新增成员奖金 团
    `activity`: 参加活动收益 奖
    """
    queryset = CarryLog.objects.all().order_by('-carry_date')
    serializer_class = serializers.CarryLogSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm
        return self.queryset.filter(xlmm=xlmm.id)  # 对应的carrylog记录

    @list_route(methods=['get'])
    def get_carryinlog(self, request):
        """获取收入内容"""
        queryset = self.filter_queryset(self.get_owner_queryset(request).filter(carry_type=CarryLog.CARRY_IN)).exclude(
            log_type__in=(CarryLog.THOUSAND_REBETA, CarryLog.COST_FLUSH, CarryLog.RECHARGE))
        groupclgs = queryset.values("carry_date", "log_type", "xlmm"
                                    ).annotate(sum_value=Sum('value'),
                                               type_count=Count('log_type')).order_by('-carry_date')
        clgs = groupclgs[0:100] if len(groupclgs) > 100 else groupclgs
        for i in clgs:
            xlmm = i['xlmm']
            i['sum_value'] = i['sum_value'] / 100.0
            carry_date = i['carry_date']
            if i['log_type'] == CarryLog.CLICK_REBETA:  # 点击类型获取点击数量
                clks = ClickCount.objects.filter(linkid=xlmm, date=carry_date)
                i['type_count'] = clks.aggregate(cliknum=Sum('valid_num')).get('cliknum') or 0
            elif i['log_type'] == CarryLog.ORDER_REBETA:  # 订单返利　则获取返利单数
                lefttime = carry_date
                righttime = carry_date + datetime.timedelta(days=1)
                shopscount = StatisticsShopping.objects.filter(linkid=xlmm, shoptime__gte=lefttime,
                                                               shoptime__lt=righttime,
                                                               status__in=(StatisticsShopping.FINISHED,
                                                                           StatisticsShopping.WAIT_SEND)).count()
                i['type_count'] = shopscount
            else:
                i['type_count'] = 0
        return Response(clgs)

    def list(self, request, *args, **kwargs):
        """
        2016-2-29 ，　由于前端接口判定为收益接口，　本接口只能过滤处收益内容！！！
        """
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        queryset = queryset.filter(carry_type=CarryLog.CARRY_IN,
                                   log_type__in=(
                                       CarryLog.ORDER_REBETA, CarryLog.CLICK_REBETA,
                                       CarryLog.THOUSAND_REBETA, CarryLog.AGENCY_SUBSIDY,
                                       CarryLog.MAMA_RECRUIT, CarryLog.ORDER_RED_PAC,
                                       CarryLog.FANSCARRY, CarryLog.GROUPBONUS,
                                       CarryLog.ACTIVITY
                                   ))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def get_clk_list(self, request):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        queryset = queryset.filter(log_type=CarryLog.CLICK_REBETA).exclude(status=CarryLog.CANCELED).order_by(
            '-carry_date')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response()

    @list_route(methods=['get'])
    def list_base_data(self, request):
        """  账户基本信息页面显示　"""
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        yestoday = datetime.date.today() - datetime.timedelta(days=1)
        qst_confirm_in = queryset.filter(carry_type=CarryLog.CARRY_IN, status=CarryLog.CONFIRMED)
        qst_confirm_out = queryset.filter(carry_type=CarryLog.CARRY_OUT, status=CarryLog.CONFIRMED)
        qst_yst_confirm_in = queryset.filter(carry_type=CarryLog.CARRY_IN, status=CarryLog.CONFIRMED,
                                             carry_date=yestoday)
        qst_yst_confirm_out = queryset.filter(carry_type=CarryLog.CARRY_OUT, status=CarryLog.CONFIRMED,
                                              carry_date=yestoday)
        qst_pending = queryset.filter(status=CarryLog.PENDING)

        mci = (qst_confirm_in.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0
        mco = (qst_confirm_out.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0
        ymci = (qst_yst_confirm_in.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0
        ymco = (qst_yst_confirm_out.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0
        pdc = (qst_pending.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0
        data = {"mci": mci, "mco": mco, "ymci": ymci, "ymco": ymco, "pdc": pdc}
        return Response(data)


class ClickCountViewSet(viewsets.ModelViewSet):
    """
    ## 特卖平台－小鹿妈妈点击API:
    - {prefix}[.format]: 获取登陆用户的点击记录
    - {prefix}/list_base_data　method:get : 当天的点击统计记录
    """
    queryset = ClickCount.objects.all()
    serializer_class = serializers.ClickCountSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm
        return self.queryset.filter(linkid=xlmm.id)  # 对应的xlmm的点击统计

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response()

    @list_route(methods=['get'])
    def list_base_data(self, request):
        today = datetime.date.today()
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        tqs = queryset.filter(date=today)  # 今天的统计记录
        serializer = self.get_serializer(tqs, many=True)
        return Response(serializer.data)


class StatisticsShoppingViewSet(viewsets.ModelViewSet):
    """
    ## 特卖平台－小鹿妈妈购买统计API:
    - {prefix}[.format]: 获取登陆用户的购买统计记录
    - {prefix}/today_shops　method:get : 当天的购买统计记录
    - {prefix}/days_num?days=[days] method: get : 过去days天每天的推广交易数量
    - {prefix}/shops_by_day?days=[days] method: get :获取days天前当天的订单数量,没有参数则返回days=0的对应数据
        `shops_num:` 订单数量
    """
    queryset = StatisticsShopping.objects.all()
    serializer_class = serializers.StatisticsShoppingSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm
        return self.queryset.filter(linkid=xlmm.id)  # 对应的xlmm的购买统计

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request)).order_by('-shoptime')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response()

    def get_tzone_queryset(self, days, request):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        today = datetime.datetime.today()
        tf = datetime.datetime(today.year, today.month, today.day, 0, 0, 0) - datetime.timedelta(days=days)
        tt = datetime.datetime.now()
        tqs = queryset.filter(shoptime__gte=tf, shoptime__lte=tt)
        return tqs

    @list_route(methods=['get'])
    def days_num(self, request):
        """ 根据给的天数，返回天数内每天的专属订单的数量　"""
        days = int(request.GET.get('days', 0))
        data = [(self.get_tzone_queryset(days=i, request=request).filter(status__in=(
            StatisticsShopping.FINISHED,
            StatisticsShopping.WAIT_SEND)).count())
                for i in range(0, days)]
        data_cp = data
        d = [data[i] - data_cp[i - 1] for i in range(days)[::-1] if i > 0]
        d.append(data[0])
        return Response(d[::-1])

    def get_xlmm(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm
        return xlmm

    @list_route(methods=['get'])
    def shops_by_day(self, request):
        """　
        根据日期参数传该日期的订单数量　
        当天点击数量和点击佣金
        """
        content = request.GET
        days = content.get("days", 0)
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        days = int(days)
        today = datetime.date.today()  # 今天日期
        target_date = today - datetime.timedelta(days=days)
        target_date_end = target_date + datetime.timedelta(days=1)
        # 获取当天的点击数量
        xlmm = self.get_xlmm(request)
        clicks = Clicks.objects.filter(linkid=xlmm.id, click_time__gte=target_date,
                                       click_time__lt=target_date_end).count()  # 点击数量
        # 获取当天的点击佣金
        mmclgs = CarryLog.objects.filter(xlmm=xlmm.id, carry_date=target_date, log_type=CarryLog.CLICK_REBETA,
                                         status__in=(CarryLog.CONFIRMED, CarryLog.PENDING))  # 点击佣金
        click_income = mmclgs.aggregate(sum_value=Sum('value')).get('sum_value') or 0
        click_money = click_income / 100.0 if click_income > 0 else 0
        qses = queryset.filter(shoptime__gte=target_date, shoptime__lt=target_date_end,
                               status__in=(StatisticsShopping.FINISHED, StatisticsShopping.WAIT_SEND))
        serializer = self.get_serializer(qses, many=True)
        return Response({'shops': serializer.data, "clicks": clicks, "click_money": click_money})


class CashOutViewSet(viewsets.ModelViewSet, PayInfoMethodMixin):
    """
    ### 特卖平台－小鹿妈妈购提现记录API:
    - {prefix}[.format]: 获取登陆用户的提现记录
    - {prefix} method[post][arg:choice("c1":80,"c2":200)]: 创建提现记录
        :return `code`
        1: 参数错误
        2: 不足提现金额
        3: 有待审核记录不予再次提现
        0: 提现成功，待审核通过
    - {prefix}/cancal_cashout [method:post] [id:id]　：　取消提现记录
        :return `code`
        `0`: 取消成功
        `1`: 取消失败
        `2`: 提现记录不存在
    - [/rest/v1/pmt/cashout/exchange_deposit](/rest/v1/pmt/cashout/exchange_deposit) 用户使用代理钱包续费代理时间;
        1. method: post
        2. args:
            * `exchange_type`: half: 半年(99元), full: 一年(188元)
        3. return:
            * {"code": 0, "info": "兑换成功!"}
            * {"code": 1, "info": "参数错误!"}
            * {"code": 2, "info": "余额不足"}
    """
    queryset = CashOut.objects.all().order_by('-created')
    serializer_class = serializers.CashOutSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)
    cashout_type = {"c1": 10000, "c2": 20000}

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm
        return self.queryset.filter(xlmm=xlmm.id)  # 对应的xlmm的购买统计

    @list_route(methods=['get'])
    def get_could_cash_out(self, request):
        """ 获取可以提现的金额 """
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm
        try:
            fortune = MamaFortune.objects.get(mama_id=xlmm.id)
            could_cash_out = fortune.cash_num_display()
        except Exception, exc:
            raise APIException(u'{0}'.format(exc.message))
        # could_cash_out = xlmm.get_cash_iters()  # 可以提现的金额
        return Response({"could_cash_out": could_cash_out})

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_customer_and_xlmm(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm
        if not xlmm.status == XiaoluMama.EFFECT:
            xlmm = None
        if not customer.status == Customer.NORMAL:
            customer = None
        return customer, xlmm

    def verify_cashout(self, cash_type, cashout_amount, customer, xlmm):

        if (cash_type is None) and (cashout_amount is None):  # 参数错误(没有参数)
            return 0, {"code": 1, "msg": '暂未开通'}

        if cash_type:
            value = self.cashout_type.get(cash_type)
        elif cashout_amount:
            value = int(decimal.Decimal(cashout_amount) * 100)
        else:
            return 0, {"code": 1, "msg": '提现金额不能为0'}

        could_cash_out, active_value_num = get_mamafortune(xlmm.id)
        # if active_value_num < 100:
        #     return 0, {"code": 4, 'msg': '活跃值不足'}  # 活跃值不够
        if self.queryset.filter(status=CashOut.PENDING, xlmm=xlmm.id).count() > 0:  # 如果有待审核提现记录则不予再次创建记录
            return 0, {"code": 3, 'msg': '提现审核中'}
        if could_cash_out < value * 0.01:  # 如果可以提现金额不足
            return 0, {"code": 2, 'msg': '余额不足'}
        return value, {"code": 0, 'msg': '提交成功'}

    def create(self, request, *args, **kwargs):
        """代理提现"""
        content = request.data
        cash_type = content.get('choice', None)
        cashout_amount = content.get('cashout_amount', None)

        customer, xlmm = self.get_customer_and_xlmm(request)
        if not (xlmm and customer):
            info = u'你的帐号异常，请联系管理员！'
            return Response({"code": 10, "info": info})

        if not xlmm.is_cashoutable():
            return Response({"code": 5, 'msg': '只有正式小鹿妈妈会员才可大额提现！'})

        value, msg = self.verify_cashout(cash_type, cashout_amount, customer, xlmm)
        if value <= 0:
            return Response(msg)

        # 满足提现请求　创建提现记录
        cash_out_type = CashOut.RED_PACKET
        uni_key = CashOut.gen_uni_key(xlmm.id, cash_out_type)
        date_field = datetime.date.today()

        cashout = CashOut(xlmm=xlmm.id, value=value, cash_out_type=cash_out_type,
                          approve_time=datetime.datetime.now(), date_field=date_field, uni_key=uni_key)
        cashout.save()

        log_action(request.user, cashout, ADDITION, u'{0}用户提交提现申请！'.format(customer.id))
        return Response(msg)

    @list_route(methods=['post', 'get'])
    def can_cashout_once(self, request):
        """
        /rest/v1/pmt/cashout/can_cashout_once
        """
        customer, mama = self.get_customer_and_xlmm(request)
        if not (mama and customer):
            info = u'你的帐号异常，请联系管理员！'
            return Response({"code": 10, "info": info})

        mama_id = mama.id
        cash_out_type = CashOut.RED_PACKET

        count = CashOut.objects.filter(xlmm=mama_id, cash_out_type=cash_out_type).exclude(status=CashOut.REJECTED).exclude(status=CashOut.CANCEL).count()
        if count > 0:
            res = Response({"code": 1, "info": u"您的首次网页提现已使用，下载APP登录可多次提现！"})
        else:
            res = Response({"code": 0, "info": u"可以提现"})

        return res

    @list_route(methods=['post', 'get'])
    def cashout_once(self, request):
        """
        /rest/v1/pmt/cashout/cashout_once
        amount=1.5 #金额1.5元
        verify_code=123456 #验证码123456
        """
        from shopback.monitor.models import XiaoluSwitch

        switch = XiaoluSwitch.objects.filter(id=7).first()
        if switch and switch.status == 1:
            return Response({"code": 2, "info": u"系统维护中，请稍后再试!"})

        customer, mama = self.get_customer_and_xlmm(request)
        if not (mama and customer):
            info = u'你的帐号异常，请联系管理员！'
            return Response({"code": 10, "info": info})
        mama_id = mama.id
        cash_out_type = CashOut.RED_PACKET

        count = CashOut.objects.filter(xlmm=mama_id, cash_out_type=cash_out_type) \
            .exclude(status=CashOut.REJECTED)  \
            .exclude(status=CashOut.CANCEL).count()
        if count > 0:
            return Response({"code": 1, "info": u"由于微信提现请求繁忙，网页提现仅限首次使用，下载APP登录即可多次提现！"})

        return self.noaudit_cashout(request)

    @list_route(methods=['post', 'get'])
    def noaudit_cashout(self, request):
        """
        /rest/v1/pmt/cashout/noaudit_cashout
        amount=1.5 #金额1.5元
        verify_code=123456 #验证码123456
        """
        content = request.data or request.GET

        amount = content.get('amount', None)  # 以元为单位
        verify_code = content.get('verify_code', None)

        if not (amount and verify_code):
            info = u'金额或验证码错误!'
            return Response({"code": 1, "info": info})

        from shopback.monitor.models import XiaoluSwitch
        if XiaoluSwitch.is_switch_open(5):
            return Response({"code": 11, "info": '系统维护，提现功能暂时关闭!'})

        customer, mama = self.get_customer_and_xlmm(request)
        if not (mama and customer):
            info = u'你的帐号异常，请联系管理员！'
            return Response({"code": 10, "info": info})

        mobile = customer.mobile
        if not (mobile and mobile.isdigit() and len(mobile) == 11):
            info = u'提现请先至个人中心绑定手机号，以便接收验证码！'
            return Response({"code": 8, "info": info})

        from flashsale.restpro.v2.views.verifycode_login import validate_code
        if not validate_code(mobile, verify_code):
            # info = u'快速提现功能内部测试中，请等待粉丝活动开始！'
            info = u'验证码不对或已过期，请重新发送验证码！'
            return Response({"code": 9, "info": info})

        from flashsale.restpro.v2.views.xiaolumm import CashOutPolicyView
        min_cashout_amount = CashOutPolicyView.MIN_CASHOUT_AMOUNT
        audit_cashout_amount = CashOutPolicyView.AUDIT_CASHOUT_AMOUNT

        amount = int(decimal.Decimal(amount) * 100)  # 以分为单位(提现金额乘以100取整)
        if amount > audit_cashout_amount:
            info = u'快速提现金额不得超过%d元!' % int(audit_cashout_amount * 0.01)
            return Response({"code": 2, "info": info})

        if amount < min_cashout_amount:
            info = u'提现金额不得低于%d元!' % int(min_cashout_amount * 0.01)
            return Response({"code": 3, "info": info})

        if not mama.is_noaudit_cashoutable():
            info = u'您的店铺尚未激活，不满足快速提现条件!请点击公众号菜单［我的店铺］激活！'
            return Response({"code": 4, "info": info})

        mama_id = mama.id
        mf = MamaFortune.objects.filter(mama_id=mama_id).first()
        pre_cash = mf.cash_num_cents()
        if pre_cash < amount:
            info = u'提现额不能超过帐户余额！'
            return Response({"code": 5, "info": info})

        if CashOut.is_cashout_limited(mama_id):
            info = u'今日提现次数已达上限，请明天再来哦！'
            return Response({"code": 6, "info": info})

        cash_out_type = CashOut.RED_PACKET
        cash_out_time = datetime.datetime.now()
        uni_key = CashOut.gen_uni_key(mama_id, cash_out_type)
        date_field = datetime.date.today()
        wx_union = WeixinUnionID.objects.get(app_key=settings.WXPAY_APPID, unionid=mama.openid)
        mama_memo = u"小鹿妈妈编号:{mama_id},提现前:{pre_cash}".format(mama_id=mama_id, pre_cash=pre_cash)
        body = u'一份耕耘，一份收获，谢谢你的努力！'

        with transaction.atomic():
            cashout = CashOut(xlmm=mama_id, value=amount, cash_out_type=cash_out_type, approve_time=cash_out_time,
                              date_field=date_field, uni_key=uni_key)
            cashout.save()
            logger.info({
                'action': 'xlmm.cashout',
                'mama_id': mama_id,
                'amount': amount
            })

            en = Envelop(referal_id=cashout.id, amount=amount, recipient=wx_union.openid,
                         platform=Envelop.WXPUB, subject=Envelop.CASHOUT, status=Envelop.WAIT_SEND,
                         receiver=mama_id, body=body, description=mama_memo)
            en.save()
            logger.info({
                'action': 'xlmm.cashout.envelop',
                'mama_id': mama_id,
                'cashout_id': cashout.id,
                'amount': amount,
                'status': Envelop.WAIT_SEND,
                'desc': mama_memo
            })
        en.send_envelop()

        return Response({"code": 0, "info": u'提交成功！'})

    @list_route(methods=['post'])
    def cashout_to_budget(self, request):
        """ 代理提现到用户余额 """
        cashout_amount = request.data.get('cashout_amount', None)
        customer, xlmm = self.get_customer_and_xlmm(request)
        if not (xlmm and customer):
            info = u'你的帐号异常，请联系管理员！'
            return Response({"code": 10, "info": info})

        if not xlmm.is_cashoutable():
            return Response({"code": 5, 'msg': '只有正式妈妈会员才可大额提现'})

        value, msg = self.verify_cashout(None, cashout_amount, customer, xlmm)
        if value <= 0:
            return Response(msg)

        # 创建Cashout
        cash_out_type = CashOut.USER_BUDGET
        uni_key = CashOut.gen_uni_key(xlmm.id, cash_out_type)
        date_field = datetime.date.today()

        cashout = CashOut(xlmm=xlmm.id,
                          value=value,
                          cash_out_type=CashOut.USER_BUDGET,
                          approve_time=datetime.datetime.now(),
                          status=CashOut.APPROVED,
                          date_field=date_field,
                          uni_key=uni_key)
        cashout.save()
        log_action(request.user.id, cashout, ADDITION, '代理提现到余额')

        budget_type = BudgetLog.BUDGET_IN
        budget_log_type = BudgetLog.BG_MAMA_CASH
        uni_key = BudgetLog.gen_uni_key(customer.id, budget_type, budget_log_type)
        BudgetLog.objects.create(customer_id=customer.id,
                                 flow_amount=value,
                                 budget_type=budget_type,
                                 referal_id=cashout.id,
                                 budget_log_type=budget_log_type,
                                 status=BudgetLog.CONFIRMED,
                                 uni_key=uni_key)
        info = '提交成功'
        return Response({"code": 0, 'msg': info, 'info': info})

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('method not allowed')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('method not allowed')

    @list_route(methods=['post'])
    def cancal_cashout(self, request):
        """ 取消提现 接口 """
        pk = request.data.get("id", None)
        queryset = self.get_owner_queryset(request).filter(id=pk)
        if queryset.exists():
            cashout = queryset[0]
            result = cashout.cancel_cashout()
            code = 0 if result else 1
            return Response({"code": code})  # 0　体现取消成功　1　失败
        return Response({"code": 2})  # 提现记录不存在

    @list_route(methods=['get'])
    def exchange_coupon(self, request):
        """
        代理余额兑换优惠券
        """
        content = request.GET
        exchange_num = content.get("exchange_num") or None  # 兑换张数
        template_id = content.get("template_id") or None  # 兑换的优惠券模板　72: ￥20　73　￥50

        default_return = collections.defaultdict(code=0, info='兑换成功')
        if not (exchange_num and template_id):
            default_return.update({"code": 1, "info": "参数错误"})
            return Response(default_return)

        tpl = CouponTemplate.objects.filter(id=template_id).first()
        if not tpl:
            default_return.update({"code": 2, "info": "优惠券还没有开放"})
            return Response(default_return)

        customer, xlmm = self.get_customer_and_xlmm(request)
        if not (xlmm and customer):
            info = u'你的帐号异常，请联系管理员！'
            return Response({"code": 10, "info": info})

        if not xlmm:
            default_return.update({"code": 3, "info": "用户异常"})
            return Response(default_return)

        could_cash_out, _ = get_mamafortune(xlmm.id)  # 可提现的金额
        exchange_amount = int(exchange_num) * tpl.value
        if exchange_amount > could_cash_out:
            default_return.update({"code": 4, "info": "兑换额超过余额"})
            return Response(default_return)

        def exchange_one_coupon():
            cash_out_type = CashOut.EXCHANGE_COUPON
            uni_key = CashOut.gen_uni_key(xlmm.id, cash_out_type)
            date_field = datetime.date.today()

            cash = CashOut(xlmm=xlmm.id,
                           value=tpl.value * 100,
                           cash_out_type=cash_out_type,
                           approve_time=datetime.datetime.now(),
                           status=CashOut.APPROVED,
                           date_field=date_field,
                           uni_key=uni_key)
            cash.save()
            log_action(request.user, cash, ADDITION, u'用户现金兑换优惠券添加提现记录')
            cou, co, ms = UserCoupon.objects.create_cashout_exchange_coupon(customer.id, tpl.id,
                                                                            cashout_id=cash.id)
            if co != 0:
                cash.status = CashOut.CANCEL
                cash.save(update_fields=['status'])
                log_action(request.user, cash, CHANGE, u'优惠券兑换失败，自动取消提现记录')
            return cash.id, cou, co, ms

        codes = []
        msgs = []
        for i in xrange(int(exchange_num)):
            try:
                cashout_id, coupon, c_code, msg = exchange_one_coupon()
                codes.append(c_code)
                msgs.append(msg)
            except AssertionError as e:
                msgs.append(e.message)
                logger.error(u'exchange_coupon %s' % e)
                continue
        success_num = codes.count(0)  # 发放成功的数量
        if success_num > 0:
            default_return.update({"info": "成功兑换%s张优惠券" % success_num})
            return Response(default_return)
        default_return.update({"code": 5, "info": "兑换出错:%s" % '/'.join(msgs)})
        return Response(default_return)

    @list_route(methods=['post'])
    def exchange_deposit(self, request):
        """
        代理钱包余额兑换代理费用(续费)
        """
        exchange_type = request.data.get('exchange_type') or None
        exchange_type_map = {'half': 99, 'full': 188}
        days_map = {'half': XiaoluMama.HALF, 'full': XiaoluMama.FULL}

        customer, xlmm = self.get_customer_and_xlmm(request)
        if not (xlmm and customer):
            info = u'你的帐号异常，请联系管理员！'
            return Response({"code": 10, "info": info})

        default_return = collections.defaultdict(code=0, info='兑换成功!')
        if exchange_type not in exchange_type_map:
            default_return.update({"code": 1, "info": "参数错误!"})
            return Response(default_return)
        deposit = exchange_type_map[exchange_type]
        could_cash_out, _ = get_mamafortune(xlmm.id)  # 可提现的金额(元)

        if deposit > could_cash_out:
            default_return.update({"code": 2, "info": "余额不足"})
            return Response(default_return)
        try:
            from flashsale.coupon.tasks import task_release_coupon_for_mama_deposit, \
                task_release_coupon_for_mama_deposit_double_99

            if xlmm.last_renew_type == XiaoluMama.HALF:
                task_release_coupon_for_mama_deposit_double_99.delay(customer.id)
            else:
                task_release_coupon_for_mama_deposit.delay(customer.id, days_map[exchange_type])

        except Exception as exc:
            logger.warn({'action': 'mama_exchange_deposit', 'mama_id': xlmm.id,
                         'exchange_type': exchange_type, 'message': exc.message})
            # 这里是续费　如果是第一次成为正式的话(发送优惠券)　否则异常打入log 后继续续费动作
        cash = CashOut(xlmm=xlmm.id,
                       value=deposit * 100,
                       cash_out_type=CashOut.MAMA_RENEW,
                       approve_time=datetime.datetime.now(),
                       status=CashOut.APPROVED)
        cash.save()
        log_action(request.user, cash, ADDITION, u'用户妈妈钱包兑换代理续费')
        # 延迟 XiaoluMama instance 的续费时间　如果续费时间大于当前时间并且　当前instance 是冻结的则解冻
        days = days_map[exchange_type]
        xlmm.update_renew_day(days)
        log_action(request.user, xlmm, CHANGE, u'用户妈妈钱包兑换代理续费修改字段')
        potential = PotentialMama.objects.filter(potential_mama=xlmm.id).first()  # 续费的潜在妈妈
        if potential:
            extra = {"cashout_id": cash.id}
            state = potential.update_full_member(last_renew_type=xlmm.last_renew_type, extra=extra)  # 续费转正
            if state:
                log_action(request.user, potential, CHANGE, u'用户钱包兑换妈妈续费')
        return Response(default_return)


class ClickViewSet(viewsets.ModelViewSet):
    """
    ## 特卖平台－代理专属链接点击记录API:
    - {prefix}[.format]: 获取登陆代理用户的点击记录
    - {prefix}/click_by_day?days=[days][.format]　[method:get] : 获取当前代理的指定days天数的所有点击佣金额 和　按天数的点击记录
    :return
    `all_income`: 所有点击的佣金金额
    `results`: 点击记录
    """
    queryset = Clicks.objects.all()
    serializer_class = serializers.ClickSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm
        return self.queryset.filter(linkid=xlmm.id)  # 对应的xlmm的点击记录

    def get_owner_xlmm(self, request):
        """ 返回当前用户的代理对象(如果存在的话) """
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm
        return xlmm  # 对应的xlmm

    @list_route(methods=['get'])
    def click_by_day(self, request):
        """ 计算当前代理用户的今日点击佣金和所有点击佣金 """
        content = request.GET
        days = content.get("days", 0)
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        days = int(days)
        today = datetime.date.today()  # 今天日期
        target_date = today - datetime.timedelta(days=days)
        target_date_end = target_date + datetime.timedelta(days=1)
        today_clicks = queryset.filter(click_time__gte=target_date,
                                       click_time__lt=target_date_end).order_by('-click_time')
        data = []
        for click in today_clicks:
            dic = model_to_dict(click, fields=['isvalid', 'click_time'])
            data.append(dic)

        xlmm = self.get_owner_xlmm(request)
        mmclgs = CarryLog.objects.filter(xlmm=xlmm.id, log_type=CarryLog.CLICK_REBETA,
                                         status__in=(CarryLog.CONFIRMED, CarryLog.PENDING))  # 总计点击佣金
        mmclgs_all_income = mmclgs.aggregate(sum_value=Sum('value')).get('sum_value') or 0
        all_income = mmclgs_all_income / 100.0 if mmclgs_all_income > 0 else 0
        return Response({"all_income": all_income, "results": data})

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request)).order_by('-click_time')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException("method not allowed")

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException("method not allowed")

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException("method not allowed")
