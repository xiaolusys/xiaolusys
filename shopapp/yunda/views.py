# -*- coding:utf8 -*-
import os, re, json
import datetime
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.db.models import Sum, Count, Max
# from djangorestframework import status
# from djangorestframework.response import Response,ErrorResponse
from shopback import paramconfig as pcfg
from shopback.logistics.models import LogisticsCompany
from shopback.base.views import FileUploadView_intercept
from core.options import log_action, ADDITION, CHANGE
from .service import YundaPackageService, DEFUALT_CUSTOMER_CODE
from .models import (BranchZone,
                     YundaCustomer,
                     LogisticOrder,
                     ParentPackageWeight,
                     TodaySmallPackageWeight,
                     TodayParentPackageWeight,
                     JZHW_REGEX,
                     YUNDA,
                     NORMAL,
                     DELETE)
from .options import get_addr_zones
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
from rest_framework import status
from shopback.base.new_renders import new_BaseJSONRenderer


class PackageByCsvFileView(FileUploadView_intercept):
    serializer_class = serializers.PackageListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer, BrowsableAPIRenderer)
    file_path = 'yunda'
    filename_save = 'package_%s.csv'

    def get(self, request, *args, **kwargs):
        pass
        return Response({"example": "get_function"})

    def getSid(self, row):
        return row[0]

    def getParentSid(self, row):
        return row[6]

    def getPackDestinate(self, row):
        return row[7]

    def isJZHW(self, row):
        return JZHW_REGEX.match(row[7]) and True or False

    def getYundaPackageRegex(self):
        yunda_company = LogisticsCompany.objects.get(code=YUNDA)
        return re.compile(yunda_company.reg_mail_no)

    def createParentPackage(self, row):

        psid = self.getParentSid(row)
        if len(psid) < 13 or not psid.startswith('9'):
            return

        ppw, state = ParentPackageWeight.objects.get_or_create(
            parent_package_id=psid)
        ppw.is_jzhw = self.isJZHW(row)
        ppw.destinate = self.getPackDestinate(row)
        ppw.save()

        tppw, state = TodayParentPackageWeight.objects.get_or_create(
            parent_package_id=psid)
        tppw.is_jzhw = self.isJZHW(row)
        tppw.save()

    def createSmallPackage(self, row):

        sid = self.getSid(row)
        psid = self.getParentSid(row)

        lo, sate = LogisticOrder.objects.get_or_create(out_sid=sid)
        lo.parent_package_id = psid
        lo.is_jzhw = self.isJZHW(row)
        lo.save()

        tspw, state = TodaySmallPackageWeight.objects. \
            get_or_create(package_id=sid)
        tspw.parent_package_id = psid
        tspw.is_jzhw = self.isJZHW(row)
        tspw.save()

    def createTodayPackageWeight(self, row):

        self.createSmallPackage(row)

        self.createParentPackage(row)

    def handle_post(self, request, csv_iter):

        package_regex = self.getYundaPackageRegex()
        encoding = self.getFileEncoding(request)

        for row in csv_iter:
            if package_regex.match(row[0]) and not row[0].startswith('9'):
                row = [r.strip().decode(encoding) for r in row]
                self.createTodayPackageWeight(row)

        return Response({'success': True,
                         'redirect_url': reverse('admin:yunda_todaysmallpackageweight_changelist')})


class CustomerPackageImportView(FileUploadView_intercept):
    serializer_class = serializers.PackageListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer, BrowsableAPIRenderer)
    file_path = 'yunda'
    filename_save = 'cr_package_%s.csv'

    def get(self, request, *args, **kwargs):
        print "get"
        pass
        return Response({"example": "get_function"})

    def getCustomer(self, code):
        try:
            return YundaCustomer.objects.get(code=code)
        except:
            raise Exception(u'未找到代码(%s)对应的客户信息' % code)

    def getSid(self, row):
        return row[2]

    def getCusOid(self, row):
        return row[0]

    def getPackageCompany(self, row):
        return row[1]

    def getPackageReceiver(self, row):
        return row[3]

    def getPackageState(self, row):
        return row[4]

    def getPackageCity(self, row):
        return row[5]

    def getPackageDistrict(self, row):
        return row[6]

    def getPackageAddress(self, row):
        return row[7]

    def getPackageMobile(self, row):
        return row[8]

    def getPackagePhone(self, row):
        return row[9]

    def isValidPackage(self, row):

        yunda_company = LogisticsCompany.objects.get(code=YUNDA)
        return re.compile(yunda_company.reg_mail_no).match(self.getSid(row))

    def createPackageOrder(self, customer, row, ware_no):

        sid = self.getSid(row)

        lo, sate = LogisticOrder.objects.get_or_create(out_sid=sid)
        if lo.cus_oid and lo.cus_oid != self.getCusOid(row):
            raise Exception(u'运单单号:%s,新(%s)旧(%s)客户单号不一致，请核实！' %
                            (sid, lo.cus_oid, self.getCusOid(row)))

        lo.yd_customer = customer
        lo.cus_oid = self.getCusOid(row)
        lo.receiver_name = self.getPackageReceiver(row)
        lo.receiver_state = self.getPackageState(row)
        lo.receiver_city = self.getPackageCity(row)
        lo.receiver_district = self.getPackageDistrict(row)
        lo.receiver_address = self.getPackageAddress(row)
        lo.receiver_mobile = self.getPackageMobile(row)
        lo.receiver_phone = self.getPackagePhone(row)
        lo.wave_no = ware_no
        lo.save()

        tspw, state = TodaySmallPackageWeight.objects. \
            get_or_create(package_id=sid)
        tspw.is_jzhw = lo.isJZHW()
        tspw.save()

    def handle_post(self, request, csv_iter):

        wave_no = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
        encoding = self.getFileEncoding(request)
        cus_code = csv_iter.next()[0].split('-')[0]
        customer = self.getCustomer(cus_code.upper())

        for row in csv_iter:
            row = [r.strip().decode(encoding) for r in row]
            if self.isValidPackage(row):
                self.createPackageOrder(customer, row, wave_no)

        return Response({'success': True, 'redirect_url': '/admin/yunda/logisticorder/?q=' + wave_no})


class DiffPackageDataView(APIView):
    serializer_class = serializers.PackageListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (TemplateHTMLRenderer, new_BaseJSONRenderer, BrowsableAPIRenderer)
    template_name = "yunda/upload_yunda_package.html"

    def calcWeight(self, sqs, pqs):

        tspw_dict = sqs.aggregate(
            total_num=Count('package_id'),
            total_weight=Sum('weight'),
            total_upload_weight=Sum('upload_weight'))

        jb_tspw_dict = sqs.exclude(parent_package_id='').aggregate(
            total_num=Count('package_id'),
            total_weight=Sum('weight'),
            total_upload_weight=Sum('upload_weight'))

        tppw_dict = pqs.aggregate(
            total_num=Count('parent_package_id'),
            total_weight=Sum('weight'),
            total_upload_weight=Sum('upload_weight'))

        return {'A': tspw_dict, 'B': jb_tspw_dict, 'C': tppw_dict}

    def calcPackageData(self):

        small_queryset = TodaySmallPackageWeight.objects.all()
        parent_queryset = TodayParentPackageWeight.objects.all()
        print 'weight:', small_queryset.aggregate(max_weight=Max('weight'))
        return {'all': self.calcWeight(small_queryset, parent_queryset),
                'jzhw': self.calcWeight(small_queryset.filter(is_jzhw=True),
                                        parent_queryset.filter(is_jzhw=True)),
                'other': self.calcWeight(small_queryset.filter(is_jzhw=False),
                                         parent_queryset.filter(is_jzhw=False)),
                'max_sweight': small_queryset.aggregate(max_weight=Max('weight')).get('max_weight'),
                'max_pweight': parent_queryset.aggregate(max_weight=Max('weight')).get('max_weight')
                }

    def isValidLanjianUser(self, lanjian_id):

        yc = YundaCustomer.objects.get(code=DEFUALT_CUSTOMER_CODE)
        return yc.lanjian_id == lanjian_id

    def get(self, request, *args, **kwargs):

        small_queryset = TodaySmallPackageWeight.objects.all()
        parent_queryset = TodayParentPackageWeight.objects.all()
        error_packages = []

        yunda_service = YundaPackageService()

        for tspw in small_queryset:
            try:
                weight_tuple = yunda_service.calcSmallPackageWeight(tspw)
                tspw.weight = weight_tuple[0] or tspw.weight
                tspw.upload_weight = weight_tuple[1] or tspw.upload_weight
                tspw.save()
            except Exception, exc:
                error_packages.append((tspw.package_id, tspw.weight, exc.message))

        if not error_packages:
            for tppw in parent_queryset:
                try:
                    weight_tuple = yunda_service.calcParentPackageWeight(tppw)
                    tppw.weight = weight_tuple[0] or tppw.weight
                    tppw.upload_weight = weight_tuple[1] or tppw.upload_weight
                    tppw.save()
                except Exception, exc:
                    error_packages.append((tppw.parent_package_id, tppw.weight, exc.message))

        if error_packages:
            return Response({'error_packages': error_packages})

        response = self.calcPackageData()

        return Response({"object": response})

    def post(self, request, *args, **kwargs):

        lanjian_id = request.POST.get('lanjian_id', '').strip()

        try:
            if not self.isValidLanjianUser(lanjian_id):
                raise Exception(u'揽件ID不正确，重新再试！')

            parent_queryset = TodayParentPackageWeight.objects.all()

            ydpkg_service = YundaPackageService()
            for parent_package in parent_queryset:
                child_packages = TodaySmallPackageWeight.objects \
                    .filter(parent_package_id=parent_package.parent_package_id)
                ydpkg_service.uploadSmallPackageWeight(child_packages)

                ydpkg_service.uploadParentPackageWeight([parent_package])

            small_queryset = TodaySmallPackageWeight.objects.all()
            ydpkg_service.uploadSmallPackageWeight(small_queryset)

        except Exception, exc:
            messages.error(request, u'XXXXXXXXXXXXXXXXXXXXX 包裹重量上传异常:%s XXXXXXXXXXXXXXXXXXXXX' % exc.message)
        else:
            messages.info(request, u'================ 包裹重量上传成功 ===================')

        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(TodaySmallPackageWeight)

        return HttpResponseRedirect(reverse('admin:%s_%s_changelist' % (ct.app_label, ct.model)))


class PackageWeightView(APIView):
    """ 包裹称重视图 """
    serializer_class = serializers.LogisticOrderSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer, BrowsableAPIRenderer)

    def isValidYundaId(self, package_no):
        if len(package_no) < 13:
            return False

        yunda_company = LogisticsCompany.objects.get(code=YUNDA)
        return re.compile(yunda_company.reg_mail_no).match(package_no[0:13])

    def parseYundaId(self, package_no):

        if len(package_no) < 24:
            return package_no[0:13], '', ''
        return package_no[0:13], package_no[13:17], package_no[17:23]

    def getYundaZone(self, lg_order, dc_code=None):

        if dc_code:
            bzones = BranchZone.objects.filter(barcode=dc_code)
            if bzones.count() > 0:
                return bzones[0]

        return get_addr_zones(lg_order.receiver_state,
                              lg_order.receiver_city,
                              lg_order.receiver_district,
                              address=lg_order.receiver_address)

    def get(self, request, *args, **kwargs):

        content = request.REQUEST
        package_no = content.get('package_no')

        if not self.isValidYundaId(package_no):
            return u'非法的运单号'

        package_id, valid_code, dc_code = self.parseYundaId(package_no)

        try:
            lo = LogisticOrder.objects.get(out_sid=package_id)
        except LogisticOrder.DoesNotExist:
            if not dc_code:
                return u'运单号未录入系统'
            lo, state = LogisticOrder.objects.get_or_create(out_sid=package_id)
            lo.dc_code = dc_code
            lo.valid_code = valid_code
            lo.save()
            log_action(request.user.id, lo, ADDITION, u'扫描录单')
        try:
            yd_customer = lo.yd_customer and lo.yd_customer.name or ''
        except:
            yd_customer = ''

        return Response({'package_id': package_id,
                         'cus_oid': lo.cus_oid,
                         'yd_customer': yd_customer,
                         'receiver_name': lo.receiver_name,
                         'receiver_state': lo.receiver_state,
                         'receiver_city': lo.receiver_city,
                         'receiver_district': lo.receiver_district,
                         'receiver_address': lo.receiver_address,
                         'created': lo.created,
                         'zone': self.getYundaZone(lo, dc_code)
                         })

    def post(self, request, *args, **kwargs):

        content = request.REQUEST
        package_no = content.get('package_no')
        package_weight = content.get('package_weight')

        if not self.isValidYundaId(package_no):
            return u'非法的运单号'

        package_id, valid_code, dc_code = self.parseYundaId(package_no)
        try:
            lo = LogisticOrder.objects.get(out_sid=package_no)
        except LogisticOrder.DoesNotExist:
            return u'运单号未录入系统'
        try:
            float(package_weight)
        except:
            return u'重量异常:%s' % package_weight
        lo.weight = package_weight
        lo.valid_code = valid_code
        lo.dc_code = dc_code
        lo.save()

        tspw, state = TodaySmallPackageWeight.objects.get_or_create(
            package_id=package_no)
        tspw.weight = package_weight
        tspw.save()
        log_action(request.user.id, lo, CHANGE, u'扫描称重')

        return Response({'isSuccess': True})


class BranchZoneView(APIView):
    """ 获取分拨集包规则 """

    serializer_class = serializers.BranchZoneSerializer
    #     permission_classes = (permissions.IsAuthenticated,)
    #     authentication_classes = (authentication.SessionAuthentication,authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer,)

    def get(self, request, *args, **kwargs):
        content = request.REQUEST
        province = content.get('province', '')
        city = content.get('city', '')
        district = content.get('district', '')
        address = content.get('address', '')

        # branch_zone = get_addr_zones(province,city,district,address=address)
        # branch_zone  = branch_zone and serializers.BranchZoneSerializer(branch_zone).data or {}
        branch_zone = {}
        return Response({'province': province,
                         'city': city,
                         'district': district,
                         'address': address,
                         'branch_zone': branch_zone,
                         })
