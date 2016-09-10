from shopback.trades.models import TradeWuliu, PackageOrder, ReturnWuLiu
from rest_framework import serializers

class TradeWuliuSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeWuliu
        exclude = ()


class ReturnWuliuSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnWuLiu
        exclude = ()


