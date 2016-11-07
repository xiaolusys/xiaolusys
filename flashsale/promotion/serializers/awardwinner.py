from rest_framework import serializers
from ..models import AwardWinner


class AwardWinnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AwardWinner
        fields = ('customer_img', 'customer_nick', 'invite_num')
