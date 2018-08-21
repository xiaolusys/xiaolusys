# -*- coding:utf-8 -*-
__Author__ = "fang   kaienng    2015-7-24"
from shopback.items.models import Product, ProductSku
from shopback.purchases.models import Purchase, Supplier, Deposite, PurchaseType, PURCHASE_STATUS, \
    PURCHASE_ARRIVAL_STATUS, PURCHASE_STORAGE_STATUS, PAYMENT_STATUS
from shopback.purchases.models import PurchaseItem, PurchaseStorage, PurchaseStorageItem, PurchasePayment
from shopback import paramconfig as pcfg
from rest_framework import serializers


# from .models import Category

# class CategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Category
#         fields = ('cid', 'parent_cid', 'name', 'status', 'sort_order')

# class CategorySerializer(serializers.ModelSerializer):
#      
#     class Meta:
#     
#         model = Category
#         fields =  ('cid','parent_cid' ,'is_parent' ,'name','status','sort_order')
#         fields = ('parent_cid' ,'is_parent' ) 


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ('supply_type', 'supplier_name', 'contact', 'phone', 'mobile', 'fax', 'zip_code', 'email', 'address',
                  'account_bank', 'account_no', 'main_page', 'in_use', 'extra_info')


class DepositeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposite
        fields = ('deposite_name', 'location', 'in_use', 'extra_info')


class PurchaseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseType
        fields = ('type_name', 'in_use', 'extra_info')


class PurchaseSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=PURCHASE_STATUS,
                                     default=pcfg.PURCHASE_DRAFT)
    arrival_status = serializers.ChoiceField(choices=PURCHASE_ARRIVAL_STATUS,
                                             default=pcfg.PD_UNARRIVAL)

    class Meta:
        model = Purchase
        fields = ('origin_no', 'attach_files', 'id', 'unfinish_purchase_items', 'status', 'forecast_date', 'post_date',
                  'service_date', 'creator', 'created', 'modified', 'purchase_num', 'storage_num', 'total_fee',
                  'prepay', 'payment', 'receiver_name', 'arrival_status', 'extra_name', 'extra_info', 'prepay_cent')


class PurchaseItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseItem
        fields = ('id', 'supplier_item_id', 'product_id', 'sku_id', 'outer_id', 'name',
                  'outer_sku_id', 'properties_name', 'std_price', 'price', 'purchase_num', 'total_fee')
        # exclude = ('url',)


class PurchaseStorageSerialize(serializers.ModelSerializer):
    """ docstring for PurchaseStorageResource ModelResource """
    status = serializers.ChoiceField(choices=PURCHASE_STORAGE_STATUS,
                                     default=pcfg.PURCHASE_DRAFT)

    class Meta:
        model = PurchaseStorage
        fields = (
        'origin_no', 'supplier', 'forecast_date', 'deposite', 'post_date', 'created', 'modified', 'storage_num',
        'status', 'total_fee',
        'prepay', 'payment', 'logistic_company', 'out_sid', 'is_addon', 'extra_name', 'extra_info', 'is_pod',
        'attach_files')


class PurchasePaymentSerialize(serializers.ModelSerializer):
    """ docstring for PurchasePaymentResource ModelResource """
    status = serializers.ChoiceField(choices=PAYMENT_STATUS,
                                     default=pcfg.PP_WAIT_APPLY)

    class Meta:
        model = PurchasePayment
        fields = (
        'origin_nos', 'pay_type', ' pay_time', 'payment', 'supplier', 'created', 'modified', 'status', 'applier',
        'cashier', 'pay_no', 'pay_bank')
