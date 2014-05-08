#-*- coding:utf8 -*-
__author__ = 'meixqhi'
from djangorestframework.resources import ModelResource
from .models import LogisticOrder,TodaySmallPackageWeight,TodayParentPackageWeight


class PackageListResource(ModelResource):
    """ docstring for ProductList ModelResource """

    model = TodayParentPackageWeight
    fields = ('package_id','parent_package_id','weight','upload_weight','weighted',
              'is_jzhw','success','redirect_url','errorMsg','all','jzhw','other') 
    exclude = ('url',)
    
    
class LogisticOrderResource(ModelResource):
    """ docstring for ProductList ModelResource """

    model = LogisticOrder
    fields = ('package_id','cus_oid','out_sid','yd_customer','receiver_name','receiver_state','receiver_city',
              'receiver_district','receiver_address','created','zone','isSuccess') 
    exclude = ('url',)
    
    
