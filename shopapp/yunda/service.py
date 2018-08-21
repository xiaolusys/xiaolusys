# -*- coding:utf8 -*-
import time
import datetime
import json
import urllib2
import cgi
from lxml import etree
from StringIO import StringIO
from shopapp.yunda.models import YundaCustomer, LogisticOrder, ParentPackageWeight, \
    TodaySmallPackageWeight, TodayParentPackageWeight, AnonymousYundaCustomer, YUNDA_CODE, NORMAL, DELETE
from common.utils import valid_mobile, format_datetime, group_list
import logging

logger = logging.getLogger('django.request')

YUNDA_ADDR_URL = 'http://qz.yundasys.com:18080/ws/opws.jsp'
YUNDA_SCAN_URL = 'http://qz.yundasys.com:9900/ws/ws.jsp'

ADDR_UPLOAD_LIMIT = 100
WEIGHT_UPLOAD_LIMIT = 30
RETRY_INTERVAL = 60
DEFUALT_CUSTOMER_CODE = 'QIYUE'
PACKAGE_BAG_WEIGHT = 0.05


def post_yunda_service(req_url, data='', headers=None):
    """
    <dta st="ok" res="0" op="op02putdan">
    <h><ver>3.0</ver><time>2013-09-07 17:20:48</time></h>
    </dta>
    """

    # data = urllib.urlencode(data)
    req = urllib2.Request(req_url, data=data,
                          headers=headers or {'Content-Type': 'text/xml; charset=UTF-8',
                                              'Accept': '*/*',
                                              'Accept-Language': 'zh-cn',
                                              'Connection': 'Keep-Alive',
                                              'Cache-Control': 'no-cache'})
    r = urllib2.urlopen(req)
    res = r.read()

    parser = etree.XMLParser()
    tree = etree.parse(StringIO(res), parser)

    ds = tree.xpath('/dta')

    status = ds[0].attrib['st']
    if status.lower() != 'ok':
        raise Exception(res)

    return tree


class YundaService(object):
    yd_account = None

    def __init__(self, cus_code):

        self.yd_account = self.getAccount(cus_code)

    def getAccount(self, cus_code):
        try:
            return YundaCustomer.objects.get(code=cus_code)
        except:
            raise Exception(u'未找到编码(%s)对应的客户' % cus_code)

    def _getYundaYJSWData(self, obj):

        return [obj.get('valid_code', ''),
                obj['package_id'],
                None,
                '20',
                '%.2f' % obj['upload_weight'],
                '0',
                self.yd_account.cus_id,
                None,
                self.yd_account.cus_id,
                None,
                None,
                200000,
                None,
                self.yd_account.cus_id,
                '0',
                '14',
                format_datetime(obj['weighted'])]

    def _getYJSWXmlData(self, objs):

        content = []
        header = """<req op="op04chz">
                    <h>
                        <ver>1.0</ver>
                        <company>%s</company>
                        <user>%s</user>
                        <pass>%s</pass>
                        <dev1>%s</dev1>
                        <dev2>%s</dev2>
                    </h><data>""" % (self.yd_account.cus_id,
                                     self.yd_account.lanjian_id,
                                     self.yd_account.lanjian_code,
                                     self.yd_account.sn_code,
                                     self.yd_account.device_code)
        footer = "</data></req>"

        content.append(header)

        for obj in objs:

            kvs = self._getYundaYJSWData(obj)

            o = ["<o>"]
            for im in kvs:
                o.append(im and '<d>%s</d>' % im or '<d />')
            o.append("</o>")

            content.append("".join(o))

        content.append(footer)

        return "".join(content)

    def flushSmallPackageWeight(self, package):

        lo = LogisticOrder.objects.get(out_sid=package['package_id'])
        lo.upload_weight = package['upload_weight']
        lo.is_charged = True
        lo.uploaded = datetime.datetime.now()
        lo.save()

        tspw = TodaySmallPackageWeight.objects.get(package_id=package['package_id'])
        tspw.delete()

    def flushParentPackageWeight(self, package):

        ppw = ParentPackageWeight.objects.get(parent_package_id=package['package_id'])
        ppw.weight = package['weight']
        ppw.upload_weight = package['upload_weight']
        ppw.is_charged = True
        ppw.uploaded = datetime.datetime.now()
        ppw.save()

        tppw = TodayParentPackageWeight.objects.get(parent_package_id=package['package_id'])
        tppw.delete()

    def flushPackageWeight(self, yd_dict_list):

        for package in yd_dict_list:
            if package['is_parent']:
                self.flushParentPackageWeight(package)
                continue
            self.flushSmallPackageWeight(package)

    def validWeight(self, package_list):

        for package in package_list:
            if not package['upload_weight'] or float(package['upload_weight']) == 0 \
                    or float(package['upload_weight']) > 50:
                raise Exception(u'上传包裹(%s)重量(%skg)异常!' % package['package_id'])

        return True

    def uploadWeight(self, package_dict_list):

        self.validWeight(package_dict_list)

        post_xml = self._getYJSWXmlData(package_dict_list)

        post_yunda_service(YUNDA_SCAN_URL, data=post_xml.encode('utf8'))


class YundaPackageService(object):
    def _calJZHWeightRule(self, weight):

        return weight < 0.5 and weight or weight * 0.94

    def _calExternalWeightRule(self, weight):

        if weight < 0.5:
            return weight
        if weight < 1.0:
            return weight * 0.4
        if weight < 4.0:
            return weight * 0.4
        return weight * 0.4

    def _reCalcWeightRule(self, weight):

        if weight < 0.5:
            return weight
        if weight < 4.0:
            return weight * 0.4
        return weight * 0.4

    def calcSmallPackageWeight(self, tspw):

        try:
            spw = LogisticOrder.objects.get(out_sid=tspw.package_id)
        except LogisticOrder.DoesNotExist:
            raise Exception(u'小包号:%s,运单信息未入库!' % (tspw.package_id))

        if not spw.weight or float(spw.weight) <= 0:
            raise Exception(u'小包号:%s,重量为空!' % tspw.package_id)

        package_weight = float(spw.weight)

        if spw.is_jzhw:
            return round(package_weight, 2), round(self._calJZHWeightRule(package_weight), 2)

        return round(package_weight, 2), round(self._calExternalWeightRule(package_weight), 2)

    def _getSmallPackageWeightDict(self, queryset):

        ydo_list = []
        for package in queryset:
            ydo_list.append({'valid_code': '',
                             'package_id': package.package_id,
                             'weight': package.weight,
                             'upload_weight': package.upload_weight,
                             'weighted': package.weighted,
                             'is_parent': False})
        return ydo_list

    def calcParentPackageWeight(self, bpkw):

        tspws = TodaySmallPackageWeight.objects.filter(
            parent_package_id=bpkw.parent_package_id)
        bpkw_weight = 0
        bpkw_upload_weight = 0
        for tspw in tspws:
            if not tspw.weight or not tspw.upload_weight or float(tspw.weight) <= 0:
                raise Exception(u'大包号:%s,小包号:%s,没有重量,请核对!' %
                                (tspw.parent_package_id, tspw.package_id))

            bpkw_weight += float(tspw.weight)
            bpkw_upload_weight += float(tspw.upload_weight)

        if bpkw_weight - bpkw_upload_weight < 5 and not bpkw.is_jzhw:
            bpkw_upload_weight = 0

            for tspw in tspws:
                tspw.upload_weight = self._reCalcWeightRule(float(tspw.weight))
                tspw.save()
                bpkw_upload_weight += tspw.upload_weight

        return bpkw_weight, bpkw_upload_weight + PACKAGE_BAG_WEIGHT

    def _getParentPackageWeightDict(self, queryset):

        ydo_list = []
        for package in queryset:
            ydo_list.append({'valid_code': '',
                             'package_id': package.parent_package_id,
                             'weight': package.weight,
                             'upload_weight': package.upload_weight,
                             'weighted': package.weighted,
                             'is_parent': True})
        return ydo_list

    def uploadSmallPackageWeight(self, queryset):

        yd_service = YundaService(cus_code=DEFUALT_CUSTOMER_CODE)

        for yd_list in group_list(self._getSmallPackageWeightDict(queryset), WEIGHT_UPLOAD_LIMIT):
            yd_service.uploadWeight(yd_list)
            yd_service.flushPackageWeight(yd_list)

    def uploadParentPackageWeight(self, queryset):

        yd_service = YundaService(cus_code=DEFUALT_CUSTOMER_CODE)

        for yd_list in group_list(self._getParentPackageWeightDict(queryset), WEIGHT_UPLOAD_LIMIT):
            yd_service.uploadWeight(yd_list)
            yd_service.flushPackageWeight(yd_list)
