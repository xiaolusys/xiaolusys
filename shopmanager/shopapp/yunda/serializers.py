__author__ = "kaineng.fang"
# coding:utf-8
from rest_framework import serializers
from .models import (LogisticOrder, TodaySmallPackageWeight, TodayParentPackageWeight, BranchZone)


class PackageListSerializer(serializers.ModelSerializer):
    """ docstring for ProductList ModelResource """

    class Meta:
        model = TodayParentPackageWeight
        #        fields = ('package_id','parent_package_id','weight','upload_weight','weighted',
        #               'is_jzhw','success','redirect_url','errorMsg','all','jzhw','other',
        #               'max_sweight','max_pweight','error_packages')
        exclude = ('url',)


class LogisticOrderSerializer(serializers.ModelSerializer):
    """ docstring for ProductList ModelResource """

    class Meta:
        model = LogisticOrder
        #         fields = ('package_id','cus_oid','out_sid','yd_customer','receiver_name','receiver_state','receiver_city',
        #               'receiver_district','receiver_address','created','zone','isSuccess')
        exclude = ('url',)


class BranchZoneSerializer(serializers.ModelSerializer):
    """ docstring for ProductList ModelResource """

    class Meta:
        model = BranchZone
        fields = ('code', 'name', 'barcode')
        #         exclude = ('url',)
