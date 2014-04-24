#-*- coding:utf8 -*-
import re
import datetime
import json
from django.views.decorators.csrf import csrf_exempt
from djangorestframework import status
from djangorestframework.response import Response,ErrorResponse
from shopback import paramconfig as pcfg
from shopback.base.views import ModelView,ListOrCreateModelView,ListModelView
from .models import LogisticOrder,ParentPackageWeight,\
    TodaySmallPackageWeight,TodayParentPackageWeight

reg = re.compile('^(上海|江苏|浙江|安徽)'.decode('utf8'))

class PackageByCsvFileView(ModelView):
    
    def get(self, request, *args, **kwargs):
        pass
    
    def getSid(self,row):
        return row[0]
    
    def getParentSid(self,row):
        return row[6]
    
    def getPackDestinate(self,row):
        return row[7]
    
    def isJZHW(self,row):
        return reg.match(row[7]) and True or False
    
    def createParentPackage(self,row):
        
        psid = self.getParentSid(row)
        if not psid:
            return 
        
        ppw,state  = ParentPackageWeight.objects.get_or_create(
                        parent_package_id = psid)
        ppw.is_jzhw = self.isJZHW(row),
        ppw.destinate = self.getPackDestinate(row)
        ppw.save()
            
        tppw,state = TodayParentPackageWeight.objects.get_or_create(
                        parent_package_id = psid)
        tppw.is_jzhw = self.isJZHW(row)
        tppw.save()

    def createSmallPackage(self,row):
        
        sid  = self.getSid(row)
        psid = self.getParentSid(row)
        
        lo,sate = LogisticOrder.objects.get_or_create(sid=sid)
        lo.parent_package_id = psid
        lo.save()
        
        tspw,state = TodaySmallPackageWeight.objects.\
            get_or_create(package_id=sid)
        tspw.parent_package_id = psid
        tspw.is_jzhw = self.isJZHW(row)
        tspw.save()
        
    
    def createTodayPackageWeight(self,row):
        
        self.createSmallPackage(row)
            
        self.createParentPackage(row)
    
    def getPostFileEncoding(self,request):
        return request.META['HTTP_USER_AGENT'].lower().find('windows') >-1 and 'gbk' or 'utf8'

    def post(self, request, *args, **kwargs):
        
        from common.csvutils import handle_uploaded_file
        import csv
        
        attach_files = request.FILES.get('attach_files')
        if not attach_files:
            return u'文件上传错误'
        
        filename = attach_files.name
        
        if filename[filename.rfind('.'):] != '.csv':
            return '只接受csv文件格式'
        
        dt = datetime.datetime.now()
        encoding  = self.getPostFileEncoding(request)
        file_name = 'UPSP_%s.csv'%dt.strftime("%Y%m%d%H%M%S")   
        fullfile_path = handle_uploaded_file(attach_files,'tradeUpload/'+file_name)
        
        cur_category = None
        
        with open(fullfile_path, 'rb') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            spamreader.next()
            for row in spamreader:
                try:
                    row = [r.strip().decode(encoding) for r in row]
                    self.createTodayPackageWeight(row)
                except Exception,exc:
                    messages.info(request, u'商品编码(%s)，名称(%s),保存出错信息:%s'%
                                  (self.getOuterid(row),self.getProductName(row),exc.message))
                
        return {'success':True,'redirect_url':'/admin/items/product/'}     
