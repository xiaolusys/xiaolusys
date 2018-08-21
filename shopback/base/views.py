# -*- coding:utf8 -*-
# from djangorestframework.views import ModelView ,ListModelView as FrameworkListModelView
# from djangorestframework.views import InstanceModelView as FrameworkInstanceModelView
# from djangorestframework.mixins import CreateModelMixin, InstanceMixin,ReadModelMixin
from shopback.base.mixins import PaginatorMixin, CounterMixin, BatchGetMixin, DeleteModelMixin
from rest_framework.views import APIView
from rest_framework.response import Response
# from djangorestframework.views import ListOrCreateModelView as FrameworkListOrCreateModelView

# class ListOrCreateModelView(PaginatorMixin, BatchGetMixin, FrameworkListOrCreateModelView):
#     "Added Panigation function to ListOrCreateModelView"
# 
# 
# class ListModelView(InstanceMixin,PaginatorMixin,BatchGetMixin,FrameworkListModelView):
#     "Added Panigation function to ListModelView"
# 
# 
# class SimpleListView(InstanceMixin,FrameworkListModelView):
#     "docstring for view ListModelView"
#     _suffix = 'List'
# 
# 
# class CreateModelView(CreateModelMixin, ModelView):
#     """A view which provides default operations for create, against a model in the database."""
#     #_suffix = 'List'
# 
# 
# class CounterModelView(CounterMixin, ModelView):
#     """docstring for CounterModelView"""
#     _suffix = 'List'
# 
# 
# class InstanceModelView(DeleteModelMixin,FrameworkInstanceModelView):
#     """docstring for InstanceModelView"""
#     _suffix = 'Instance'
# 
# 
# class SimpleInstanceView(InstanceMixin,ReadModelMixin,ModelView):
#     "docstring for view ListModelView"
#     _suffix = 'Instance'


import os
import csv
import datetime
from django.conf import settings


def handle_uploaded_file(f, fname, file_path=settings.DOWNLOAD_ROOT):
    filename = os.path.join(file_path, fname)
    with open(filename, 'wb+') as dst:
        for chunk in f.chunks():
            dst.write(chunk)

    return filename


#   intercept    fang 2015-7-21 20:45
class FileUploadView_intercept(APIView):
    # print "file33"
    file_path = ''
    filename_save = ''

    def __init__(self, *args, **kwargs):

        if self.file_path:
            root_path = os.path.join(settings.DOWNLOAD_ROOT, self.file_path)
            if not os.path.exists(root_path):
                os.makedirs(root_path)

        super(FileUploadView_intercept, self).__init__(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        # print "get"
        pass

    def getFileEncoding(self, request):
        return request.META['HTTP_USER_AGENT'].lower().find('windows') > -1 and 'gbk' or 'utf8'

    def parseFileName(self):
        dt = datetime.datetime.now()
        return os.path.join(self.file_path, self.filename_save) % dt.strftime("%Y%m%d%H%M%S")

    def post(self, request, *args, **kwargs):
        # print "file  posthaha"
        attach_files = request.FILES.get('attach_files')
        if not attach_files:
            return Response(u'文件上传错误')

        attach_filename = attach_files.name
        if attach_filename[attach_filename.rfind('.'):] != '.csv':
            return Response(u'只接受csv文件格式')

        file_name = self.parseFileName()
        fullfile_path = handle_uploaded_file(attach_files, file_name)

        try:
            with open(fullfile_path, 'rb') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
                response = self.handle_post(request, spamreader)

        except Exception, exc:
            if settings.DEBUG:
                raise exc
            return Response({'success': False, 'errorMsg': exc.message})

        return Response(response)

    def handle_post(self, request, csv_iter):

        raise Exception(u'请实现该方法')


        ####

        # class FileUploadView(ModelView):
        #
        #     file_path     = ''
        #     filename_save = ''
        #
        #     def __init__(self,*args,**kwargs):
        #
        #         if self.file_path:
        #             root_path  = os.path.join(settings.DOWNLOAD_ROOT,self.file_path)
        #             if not os.path.exists(root_path):
        #                 os.makedirs(root_path)
        #
        #         super(FileUploadView, self).__init__(*args,**kwargs)
        #
        #     def get(self, request, *args, **kwargs):
        #         pass
        #
        #     def getFileEncoding(self,request):
        #         return request.META['HTTP_USER_AGENT'].lower().find('windows') >-1 and 'gbk' or 'utf8'
        #
        #     def parseFileName(self):
        #         dt = datetime.datetime.now()
        #         return os.path.join(self.file_path,self.filename_save)%dt.strftime("%Y%m%d%H%M%S")
        #
        #     def post(self, request, *args, **kwargs):
        #
        #         attach_files = request.FILES.get('attach_files')
        #         if not attach_files:
        #             return u'文件上传错误'
        #
        #         attach_filename = attach_files.name
        #         if attach_filename[attach_filename.rfind('.'):] != '.csv':
        #             return u'只接受csv文件格式'
        #
        #         file_name = self.parseFileName()
        #         fullfile_path = handle_uploaded_file(attach_files,file_name)
        #
        #         try:
        #             with open(fullfile_path, 'rb') as csvfile:
        #                 spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        #                 response = self.handle_post(request, spamreader)
        #
        #         except Exception,exc:
        #             if settings.DEBUG:
        #                 raise exc
        #             return {'success':False,'errorMsg':exc.message}
        #
        #         return response
        #
        #     def handle_post(self,request,csv_iter):
        #
        #         raise Exception(u'请实现该方法')
        #
