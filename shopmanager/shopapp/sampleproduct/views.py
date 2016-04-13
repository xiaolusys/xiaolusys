# coding: utf-8
import json
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response

from django.views.decorators.csrf import csrf_exempt

from .models import SampleScan, SampleProductSku, SampleProduct, ScanLinShi


# 扫描入库
@csrf_exempt
def scan_ruku(request):
    return render(request, 'scan_ruku.html')


from django.db.models import F
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.views import APIView

from rest_framework import serializers


class ScanLinShiSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanLinShi
        fields = ('id', 'pid', 'sku_id', 'title', 'sku_name', 'bar_code',
                  'scan_num', 'scan_type', 'status')


class SampleScanView(APIView):
    #     authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    serializer_class = ScanLinShiSerializer
    template_name = "scan_ruku.html"

    def get(self, request, format=None):

        lshi = ScanLinShi.objects.all()
        ls_serializers = []
        for ls in lshi:
            ls_serializers.append(ScanLinShiSerializer(ls).data)

        return Response({'lshi': ls_serializers})

    def get_Sample_By_Barcode(self, barcode):

        bar_len = len(barcode)
        len_list = range(1, bar_len)
        len_list.reverse()
        for l in len_list:
            outer_id = barcode[0:l]
            sku_code = barcode[l:]
            sp_skus = SampleProductSku.objects.filter(product__outer_id=outer_id, outer_id=sku_code)
            if sp_skus.count() > 0:
                return sp_skus[0]
        return None

    def post(self, request, format=None):

        content = request.REQUEST
        user = request.user

        scan_type = content.get('t')
        tiaoma = content.get('tiaoma', '')
        p_sku = self.get_Sample_By_Barcode(tiaoma)
        if not p_sku:
            return Response({'code': 1, 'err': u'未找到商品'})

        # 保存到临时表
        ls, state = ScanLinShi.objects.get_or_create(pid=p_sku.product.id, sku_id=p_sku.id, scan_type=scan_type)
        if state:
            ls.title = p_sku.product.title
            ls.sku_name = p_sku.sku_name
            ls.bar_code = tiaoma

        ls.scan_num = ls.scan_num + 1
        ls.save()
        #
        sls_serialize = ScanLinShiSerializer(ls)

        return Response([sls_serialize.data])


# get = post

# 查询条码
@csrf_exempt
def scan_select(request):
    post = request.POST
    tiaoma = post.get('tiaoma', '')

    if tiaoma == '':
        # 查询临时表所有数据
        lshi = ScanLinShi.objects.all()

        return render_to_response('scan_ruku.html', {'lshi': lshi})
    # 获取条码的长度
    l = len(tiaoma)
    # 商品编码
    sp_id = tiaoma[0:int(l) - 1]
    # 规格编码
    gg_id = tiaoma[-1:]

    # 查询SampleProduct
    i = SampleProduct.objects.filter(outer_id=sp_id).count()
    if i == 0:
        # 查询临时表所有数据
        lshi = ScanLinShi.objects.all()

        return render_to_response('scan_ruku.html', {'l': "条码不存在！！", 'lshi': lshi})
    else:
        p = SampleProduct.objects.get(outer_id=sp_id)
        # 商品ID
        sa_id = p.id
        sa_name = p.title
        le = SampleProductSku.objects.filter(product_id=sa_id, outer_id=gg_id).count()
        if le == 0:
            return render_to_response('scan_ruku.html', {'lshi': ''})
        else:

            # 查询SampleProductSku
            sku = SampleProductSku.objects.get(product_id=sa_id, outer_id=gg_id)
            # 规格ID
            out_id = sku.id
            size = sku.sku_name
            purchase = sku.purchase_num
            sell = sku.sell_num
            # 保存到临时表
            ls = ScanLinShi()
            ls.pid = sa_id
            ls.sku_id = out_id
            ls.title = sa_name
            ls.sku_name = size
            ls.bar_code = tiaoma

            t = post['t']

            if int(t) == 0:
                ls.scan_num = purchase
            else:
                ls.scan_num = sell
            ls.scan_type = int(t)
            ls.save()

            # 查询临时表所有数据
            lshi = ScanLinShi.objects.all()

            return render_to_response('scan_ruku.html', {'lshi': lshi})


# 显示出入表数据集合
@csrf_exempt
def scan_list(request):
    list = SampleScan.objects.all().order_by('-id')

    return render_to_response('scan_list.html', {'list': list})


# 保存到出入库表
@csrf_exempt
def scan_save(request):
    post = request.POST
    count = post["count"]
    for i in range(1, int(count)):
        index = str(str("H_") + str(i))
        status = post[index]
        if int(status) != 0:
            # 保存到扫描出入库表
            s = SampleScan()
            index1 = str(str("A_") + str(i))
            # 商品ID
            s.pid = post[index1]
            index2 = str(str("B_") + str(i))
            # 规格ID
            s.sku_id = post[index2]
            index3 = str(str("C_") + str(i))
            s.title = post[index3]
            index4 = str(str("D_") + str(i))
            s.sku_name = post[index4]
            index5 = str(str("E_") + str(i))
            s.bar_code = post[index5]
            index6 = str(str("F_") + str(i))
            s.scan_num = post[index6]
            index7 = str(str("G_") + str(i))
            t = post[index7]
            if t == u'入库扫描':

                s.scan_type = 'in'
            else:
                s.scan_type = 'out'
            s.status = status
            s.save()
            # 保存到样品规格表
            sku = SampleProductSku.objects.get(product_id=s.pid, id=s.sku_id)
            sku.storage_num = s.scan_num
            if s.scan_type == 'in':

                if int(status) == 1:
                    sku.num = int(sku.num) + int(sku.storage_num)
                    # 更改商品库存
                    sp = SampleProduct.objects.get(id=s.pid)
                    sp.num = int(sp.num) + int(sku.storage_num)
                    sp.save()
            else:

                if int(status) == 1:
                    sku.num = int(sku.num) - int(sku.storage_num)
                    # 更改商品库存
                    sp = SampleProduct.objects.get(id=s.pid)
                    sp.num = int(sp.num) - int(sku.storage_num)
                    sp.save()
            sku.save()
    # 清空临时表
    ls = ScanLinShi.objects.all()
    ls.delete()

    return HttpResponseRedirect("../scan_new/")
