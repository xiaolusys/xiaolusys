#-*- coding:utf8 -*-
__author__ = 'meixqhi'
from djangorestframework.resources import ModelResource
from .models import TodaySmallPackageWeight,TodayParentPackageWeight


class PackageListResource(ModelResource):
    """ docstring for ProductList ModelResource """

    model = TodayParentPackageWeight
    fields = ('package_id','parent_package_id','weight','upload_weight','weighted',
              'is_jzhw','success','redirect_url','errorMsg','all','jzhw','other') 
    exclude = ('url',)
    
    
