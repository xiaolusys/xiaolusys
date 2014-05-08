#-*- coding:utf8 -*-
import os,re,json
import datetime
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db.models import Sum,Count
from djangorestframework import status
from djangorestframework.response import Response,ErrorResponse
from shopback import paramconfig as pcfg
from shopback.logistics.models import LogisticsCompany
from shopback.base.views import ModelView,ListOrCreateModelView,ListModelView
from .models import BranchZone,LogisticOrder,ParentPackageWeight,TodaySmallPackageWeight\
    ,TodayParentPackageWeight,JZHW_REGEX,YUNDA,NORMAL,DELETE
from .options import get_addr_zones


class YundaFileUploadView(ModelView):
    
    file_path     = ''
    filename_save = ''
    
    def get(self, request, *args, **kwargs):
        pass
    
    def getFileEncoding(self,request):
        return request.META['HTTP_USER_AGENT'].lower().find('windows') >-1 and 'gbk' or 'utf8'
    
    def parseFileName(self):
        dt = datetime.datetime.now()
        return os.path.join(self.file_path,self.filename_save)%dt.strftime("%Y%m%d%H%M%S")
        
    def post(self, request, *args, **kwargs):
        
        from common.csvutils import handle_uploaded_file
        import csv
        
        attach_files = request.FILES.get('attach_files')
        if not attach_files:
            return u'文件上传错误'
        
        attach_filename = attach_files.name
        
        if attach_filename[attach_filename.rfind('.'):] != '.csv':
            return u'只接受csv文件格式'
        
        file_name = self.parseFileName()   
        fullfile_path = handle_uploaded_file(attach_files,file_name)
        
        try:
            with open(fullfile_path, 'rb') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
                response = self.handle_post(request, spamreader)
                
        except Exception,exc:
            return {'success':False,'errorMsg':exc.message}
        
        return response
    
    def handle_post(self,request,csv_iter):
        
        raise Exception(u'请实现该方法')
    
        

class PackageByCsvFileView(YundaFileUploadView):
    
    
    file_path     = 'yunda'
    filename_save = 'package_%s.csv'
    
    def get(self, request, *args, **kwargs):
        pass
    
    def getSid(self,row):
        return row[0]
    
    def getParentSid(self,row):
        return row[6]
    
    def getPackDestinate(self,row):
        return row[7]
    
    def isJZHW(self,row):
        return JZHW_REGEX.match(row[7]) and True or False
    
    def getYundaPackageRegex(self):
        yunda_company = LogisticsCompany.objects.get(code=YUNDA)
        return re.compile(yunda_company.reg_mail_no)
    
    def createParentPackage(self,row):
        
        psid  = self.getParentSid(row)
        if len(psid) < 13 or not psid.startswith('9'):
            return 
        
        ppw,state  = ParentPackageWeight.objects.get_or_create(
                        parent_package_id = psid)
        ppw.is_jzhw = self.isJZHW(row)
        ppw.destinate = self.getPackDestinate(row)
        ppw.save()
            
        tppw,state = TodayParentPackageWeight.objects.get_or_create(
                        parent_package_id = psid)
        tppw.is_jzhw = self.isJZHW(row)
        tppw.save()

    def createSmallPackage(self,row):
        
        sid  = self.getSid(row)
        psid = self.getParentSid(row)
        
        lo,sate = LogisticOrder.objects.get_or_create(out_sid=sid)
        lo.parent_package_id = psid
        lo.is_jzhw = self.isJZHW(row)
        lo.save()
        
        tspw,state = TodaySmallPackageWeight.objects.\
            get_or_create(package_id=sid)
        tspw.parent_package_id = psid
        tspw.is_jzhw = self.isJZHW(row)
        tspw.save()
    
    
    def createTodayPackageWeight(self,row):
        
        self.createSmallPackage(row)
            
        self.createParentPackage(row)
    
    def handle_post(self,request,csv_iter):
        
        package_regex = self.getYundaPackageRegex()
        encoding = self.getFileEncoding(request)
        
        for row in csv_iter:
            if package_regex.match(row[0]) and not row[0].startswith('9'):
                row = [r.strip().decode(encoding) for r in row]
                self.createTodayPackageWeight(row)
                
        return {'success':True,'redirect_url':'/admin/yunda/todayparentpackageweight/'}
    
   
    
class DiffPackageDataView(ModelView):
    
    def calcWeight(self,sqs,pqs):
        
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
        return {'A':tspw_dict,'B':jb_tspw_dict,'C':tppw_dict}
    
    def get(self, request, *args, **kwargs):
        
        small_queryset  = TodaySmallPackageWeight.objects.all()
        parent_queryset = TodayParentPackageWeight.objects.all()
        
        return {'all':self.calcWeight(small_queryset,parent_queryset),
                'jzhw':self.calcWeight(small_queryset.filter(is_jzhw=True),
                                       parent_queryset.filter(is_jzhw=True)),
                'other':self.calcWeight(small_queryset.filter(is_jzhw=False),
                                       parent_queryset.filter(is_jzhw=False))
                }
    
  
class PackageWeightView(ModelView):
    """ 包裹称重视图 """
    
    def isValidYundaId(self,package_no):
        if len(package_no) < 13:
            return False
        
        yunda_company = LogisticsCompany.objects.get(code=YUNDA)
        return re.compile(yunda_company.reg_mail_no).match(package_no[0:13])
        
    def parseYundaId(self,package_no):
        
        if len(package_no) < 24: 
            return package_no[0:13],'',''
        return package_no[0:13],package_no[13:17],package_no[17:23]   
    
    def getYundaZone(self,lg_order,dc_code=None):
        
        if dc_code:
            bzones = BranchZone.objects.filter(barcode=dc_code)
            if  bzones.count() > 0:
                return bzones[0]
            
        return get_addr_zones(lg_order.receiver_state,
                              lg_order.receiver_city,
                              lg_order.receiver_district,
                              address=lg_order.receiver_address)
        
    def get(self, request, *args, **kwargs):
        
        content    = request.REQUEST
        package_no = content.get('package_no')
        
        if not self.isValidYundaId(package_no):
            return u'非法的运单号'
        
        package_id,valid_code,dc_code = self.parseYundaId(package_no)
        
        try:
            lo = LogisticOrder.objects.get(out_sid=package_id)
        except LogisticOrder.DoesNotExist:
            if not dc_code:
                return u'运单号未录入系统'
            lo,state = LogisticOrder.objects.get_or_create(out_sid=package_id)
            lo.dc_code = dc_code
            lo.valid_code = valid_code
            lo.save()
            
        try:
            yd_customer = lo.yd_customer and lo.yd_customer.name or ''
        except:
            yd_customer = ''
            
        return {'package_id':package_id,
                'cus_oid':lo.cus_oid,
                'yd_customer':yd_customer,
                'receiver_name':lo.receiver_name,
                'receiver_state':lo.receiver_state,
                'receiver_city':lo.receiver_city,
                'receiver_district':lo.receiver_district,
                'receiver_address':lo.receiver_address,
                'created':lo.created,
                'zone':self.getYundaZone(lo, dc_code)
                }
    
        
    def post(self, request,*args, **kwargs):
        
        content    = request.REQUEST
        package_no = content.get('package_no')
        package_weight = content.get('package_weight')
        
        if not self.isValidYundaId(package_no):
            return u'非法的运单号'
        
        package_id,valid_code,dc_code = self.parseYundaId(package_no)
        try:
            lo = LogisticOrder.objects.get(out_sid=package_no)
        except LogisticOrder.DoesNotExist:
            return u'运单号未录入系统'
        try:
            float(package_weight)
        except:
            return u'重量异常:%s'%package_weight
        lo.weight  = package_weight
        lo.valid_code = valid_code
        lo.dc_code = dc_code
        lo.save()
        
        tspw,state = TodaySmallPackageWeight.objects.get_or_create(
                                            package_id=package_no)
        tspw.weight = package_weight
        tspw.save()
        
        return {'isSuccess':True}
    
    