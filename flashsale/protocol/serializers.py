# coding=utf-8
from rest_framework import serializers
from flashsale.protocol.models import APPFullPushMessge


class APPPushMessgeSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    target_display = serializers.CharField(source='get_target_url_display', read_only=True)
    params_url = serializers.SerializerMethodField()

    class Meta:
        model = APPFullPushMessge
        fields = (
            'id',
            'desc',
            'target_url',
            'target_display',
            'params',
            'params_url',
            'cat',
            'platform',
            'regid',
            'result',
            'status',
            'status_display',
            'push_time'
        )

    def get_params_url(self, obj):
        # type: (APPFullPushMessge) -> Optional[text_type]
        return obj.params.get('url')
