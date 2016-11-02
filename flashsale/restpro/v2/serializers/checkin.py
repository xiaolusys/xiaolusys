# encoding=utf8
from rest_framework import serializers
from flashsale.pay.models.checkin import Checkin


class CheckinSerialize(serializers.ModelSerializer):

    mama = serializers.SerializerMethodField()

    class Meta:
        model = Checkin
        fields = ('id', 'customer', 'mama', 'created')

    def get_mama(self, obj):
        mama = obj.customer.get_xiaolumm()
        if mama:
            return mama.id
        else:
            return None
