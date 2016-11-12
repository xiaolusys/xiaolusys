# -*- coding:utf-8 -*-
__author__ = 'yan.huang'
from rest_framework import serializers
from shopback.items.models import ProductSku, SkuStock, Product


class ProductSkuSerializers(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ProductSku

        fields = (
            'outer_id', 'barcode', 'quantity', 'warn_num', 'remain_num', 'wait_post_num', 'sale_num',
            'reduce_num', 'lock_num', 'sku_inferior_num', 'cost', 'std_purchase_price', 'std_sale_price', 'agent_price',
            'staff_price', 'weight', 'properties_name', 'properties_alias', 'is_split', 'is_match', 'sync_stock',
            'is_assign', 'post_check', 'created', 'modified', 'status', 'memo')
