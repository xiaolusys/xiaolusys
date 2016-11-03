# -*- coding:utf8 -*-
__author__ = 'meixqhi'
import re
import json
from django.core.urlresolvers import reverse
# from djangorestframework.views import ModelView
# from djangorestframework.response import ErrorResponse
# from djangorestframework import status

from shopback.orders.models import Order, Trade
from shopback.trades.models import MergeTrade
from shopback.items.models import Item
from shopback.users.models import User
from shopback.base.views import FileUploadView_intercept
from shopapp.memorule.models import (TradeRule,
                                     ProductRuleField,
                                     RuleMemo,
                                     ComposeRule,
                                     ComposeItem)

from rest_framework import authentication
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.compat import OrderedDict
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer
from rest_framework.views import APIView
from rest_framework import filters
from rest_framework import authentication
from . import serializers
from shopback.base.new_renders import new_BaseJSONRenderer
from rest_framework import status

CHAR_NUMBER_REGEX = re.compile('^\w+$')

import logging

logger = logging.getLogger('django.request')


def to_memo_string(memo):
    s = [memo["post"]]
    s.append(memo["addr"])
    for product in memo["data"]:
        t = [product["pid"]]
        for k, v in product["property"].iteritems():
            t.append(k + ":" + v)
        s.append("|".join(t))
    return "\r\n".join(s)


def update_trade_memo(trade_id, trade_memo, user_id):
    try:
        rule_memo, created = RuleMemo.objects.get_or_create(pk=trade_id)
        rule_memo.rule_memo = json.dumps(trade_memo)
        rule_memo.is_used = False
        rule_memo.save()
    except Exception, exc:
        return {"success": False, "message": "write memo to backend failed"}
        # 将备注信息同步淘宝后台
    #    try:
    #        ms = to_memo_string(trade_memo)
    #        response = apis.taobao_trade_memo_update(tid=trade_id,memo=ms,tb_user_id=user_id)
    #        trade_rep = response['trade_memo_update_response']['trade']
    #        if trade_rep:
    #            MergeTrade.objects.filter(tid=trade_rep['tid']).update(modified=parse_datetime(trade_rep['modified']))
    #    except:
    #        pass

    return {"success": True}


class UpdateTradeMemoView(APIView):
    serializer_class = serializers.TradeRuleSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer, BrowsableAPIRenderer)

    def get(self, request, *args, **kwargs):
        content = request.REQUEST
        params = eval(content.get("params"))

        trade_id = params.get('tid')
        user_id = params.get('sid')

        try:
            profile = User.objects.get(visitor_id=user_id)
        except User.DoesNotExist:
            return Response({"success": False, "message": "no such seller id: " + user_id})
            # raise ErrorResponse("the seller id is not record!")

        return Response(update_trade_memo(trade_id, params, user_id=profile.visitor_id))

    post = get


class ProductRuleFieldsView(APIView):
    serializer_class = serializers.TradeRuleSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer, BrowsableAPIRenderer)

    def get(self, request, *args, **kwargs):
        content = request.REQUEST

        # out_iids = content.get('out_iids')
        # out_iid_list = out_iids.split(',')
        out_iid_list = [1, 2, 3]

        product_fields = []
        for out_iid in out_iid_list:
            trade_extras = ProductRuleField.objects.filter(outer_id=out_iid)
            trade_fields = [extra.to_json() for extra in trade_extras]
            product_fields.append([out_iid, trade_fields])

        return Response(product_fields)

    post = get


class ComposeRuleByCsvFileView(FileUploadView_intercept):
    serializer_class = serializers.TradeRuleSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer, BrowsableAPIRenderer)
    file_path = 'product'
    filename_save = 'composerule_%s.csv'

    def get(self, request, *args, **kwargs):
        pass
        return Response({"example": "get__function"})

    def getSerialNo(self, row):
        return row[0]

    def getProductCode(self, row):
        return row[1]

    def getProductName(self, row):
        return row[2]

    def getSkuCode(self, row):
        return row[3]

    def getSkuName(self, row):
        return row[4]

    def getProductNum(self, row):
        return row[5]

    def createComposeRule(self, row):

        product_code = self.getProductCode(row)
        if not CHAR_NUMBER_REGEX.match(product_code):
            return

        sku_code = self.getSkuCode(row)

        cr, state = ComposeRule.objects.get_or_create(outer_id=product_code,
                                                      outer_sku_id=sku_code)

        cr.type = ComposeRule.RULE_SPLIT_TYPE
        cr.extra_info = self.getProductName(row) + self.getSkuName(row)
        cr.save()

        return cr

    def createComposeItem(self, row, rule=None):

        product_code = self.getProductCode(row)
        if not (rule and CHAR_NUMBER_REGEX.match(product_code)):
            return

        sku_code = self.getSkuCode(row)

        ci, state = ComposeItem.objects.get_or_create(compose_rule=rule,
                                                      outer_id=product_code,
                                                      outer_sku_id=sku_code)

        ci.num = self.getProductNum(row)
        ci.extra_info = self.getProductName(row) + self.getSkuName(row)
        ci.save()

    def handle_post(self, request, csv_iter):

        encoding = self.getFileEncoding(request)
        cur_rule = None

        for row in csv_iter:

            row = [r.strip().decode(encoding) for r in row]
            print row
            if self.getSerialNo(row):
                cur_rule = self.createComposeRule(row)
                continue

            self.createComposeItem(row, rule=cur_rule)

        return Response({'success': True,
                         'redirect_url': reverse('admin:memorule_composerule_changelist')})
