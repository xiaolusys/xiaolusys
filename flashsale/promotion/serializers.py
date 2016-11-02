from rest_framework import serializers
from flashsale.promotion.models import RedEnvelope, AwardWinner, ActivityProduct, ActivityEntry
from flashsale.promotion.models.stocksale import StockSale


class RedEnvelopeSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='type_display', read_only=True)
    status = serializers.CharField(source='status_display', read_only=True)
    yuan_value = serializers.FloatField(source='value_display', read_only=True)

    class Meta:
        model = RedEnvelope
        fields = ('id', 'type', 'status', 'value', 'yuan_value', 'friend_img', 'friend_nick')


class AwardWinnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AwardWinner
        fields = ('customer_img', 'customer_nick', 'invite_num')


class ActivityProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityProduct
        fields = ('id', 'model_id', 'product_name', 'product_img', 'location_id', 'pic_type', 'jump_url')


class StockSaleSerializers(serializers.ModelSerializer):
    class Meta:
        model = StockSale
