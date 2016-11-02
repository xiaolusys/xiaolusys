# -*- coding:utf-8 -*-.
from django.views.generic import View
from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from .models import PaintAccount
from shopback.trades.models import MergeTrade
from shopback.items.models import Product, ProductSku
from shopback import paramconfig as pcfg

from shopback.users.models import Customer

import json
import random

EFFECT_PROVINCES = [u'上海', u'上海市', u'江苏', u'江苏省', u'浙江', u'浙江省', u'安徽', u'安徽省']


class CreateAccountView(View):
    def get(self, request):
        content = request.GET
        pk = content.get("pk", None)

        if pk:
            pa = PaintAccount.objects.get(pk=pk)
            customer = Customer.objects.get(pk=pa.customer_id)
            response = render_to_response('create_account.html',
                                          {'customer': customer, "pa": pa},
                                          context_instance=RequestContext(request))
            return response

        creater_id = request.user.pk

        current_customer_id = 0
        accounts = PaintAccount.objects.filter(customer_id__gt=0).order_by('pk')
        total = accounts.count()
        if total > 0:
            current_customer_id = accounts[total - 1].customer_id

        customers = Customer.objects.filter(state__in=EFFECT_PROVINCES, pk__gt=current_customer_id).order_by('pk')
        customer = customers[0]

        passchars = []
        for x in range(0, 8):
            c = random.randint(0, 35)
            if c > 9:
                c = chr(87 + c)
            passchars.append(str(c))

        pw = ''.join(passchars)

        creater_id = request.user.pk

        pa = PaintAccount.objects.create(account_name=customer.nick, customer_id=customer.pk,
                                         password=pw, province=customer.state,
                                         mobile=customer.mobile, creater_id=creater_id)

        response = render_to_response('create_account.html',
                                      {'customer': customer, "pa": pa},
                                      context_instance=RequestContext(request))

        return response

    def post(self, request):
        content = request.POST
        pk = int(content.get("paint_id"))
        account_name = content.get("account_name")
        customer_id = content.get("customer_id")
        password = content.get("password")
        mobile = content.get("mobile")
        province = content.get("province")
        street_addr = content.get("street_addr")

        tb = content.get("tb")
        jd = content.get("jd")
        wx = content.get("wx")
        is_tb = 0
        is_jd = 0
        is_wx = 0
        if tb == "on":
            is_tb = 1
        if jd == "on":
            is_jd = 1
        if wx == "on":
            is_wx = 1

        try:
            pa = PaintAccount.objects.get(pk=pk)
            pa.account_name = account_name
            pa.mobile = mobile
            pa.password = password
            pa.province = province
            pa.street_addr = street_addr
            pa.is_tb = is_tb
            pa.is_jd = is_jd
            pa.is_wx = is_wx
            pa.status = 1
            pa.save()

            return redirect('/games/paint/createaccount/')
        except:
            res = {"status": "failed"}
            return HttpResponse(json.dumps(res), content_type='application/json')
