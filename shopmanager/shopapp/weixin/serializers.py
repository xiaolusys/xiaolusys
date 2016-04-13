__author__ = "kaineng.fang"
from rest_framework import serializers
from .models import WXProduct


class WeixinProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = WXProduct

# fields = ('product_id','product_list','product_ids','next','code','response')
#         exclude = ('url',)
