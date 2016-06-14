from rest_framework import serializers
from flashsale.promotion.models_freesample import RedEnvelope, AwardWinner
from flashsale.promotion.models_top10 import TOP10ActivePic


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


class Top10PicModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TOP10ActivePic
