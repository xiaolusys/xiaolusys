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
from .models import LogisticOrder,ParentPackageWeight,\
    TodaySmallPackageWeight,TodayParentPackageWeight,JZHW_REGEX,YUNDA


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
    
    