from rest_framework import serializers
from ..models.stocksale import StockSale


class StockSaleSerializers(serializers.ModelSerializer):
    class Meta:
        model = StockSale
