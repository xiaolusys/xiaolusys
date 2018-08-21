# coding=utf-8
from rest_framework import serializers
from flashsale.protocol.models import APPFullPushMessge


class APPPushMessgeSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    target_display = serializers.CharField(source='get_target_url_display', read_only=True)
    params_info = serializers.SerializerMethodField()

    class Meta:
        model = APPFullPushMessge
        fields = (
            'id',
            'desc',
            'target_url',
            'target_display',
            'params_info',
            'cat',
            'platform',
            'regid',
            'result',
            'status',
            'status_display',
            'push_time'
        )

    def get_params_info(self, obj):
        # type: (APPFullPushMessge) -> Dict[str, Any]
        from flashsale.protocol.constants import TARGET_TYPE_MODELIST, TARGET_TYPE_WEBVIEW, TARGET_TYPE_ACTIVE, \
            TARGET_TYPE_CATEGORY_PRO

        k_m = {
            TARGET_TYPE_MODELIST: [
                {'name': '款式id', 'key': 'model_id', 'value': ''}
            ],
            TARGET_TYPE_WEBVIEW: [
                {'name': '显示原生导航', 'key': 'is_native',
                 'value': ''},
                {'name': 'RUL', 'key': 'url', 'value': ''},
            ],
            TARGET_TYPE_ACTIVE: [
                {'name': '活动id', 'key': 'activity_id', 'value': ''},
                {'name': '活动URL', 'key': 'url', 'value': ''}
            ],
            TARGET_TYPE_CATEGORY_PRO: [
                {'name': '分类产品', 'key': 'cid', 'value': ''},
            ]
        }
        params = []
        if obj.target_url in k_m.keys():
            for k, v in obj.params.iteritems():
                res = {}
                for item in k_m[obj.target_url]:
                    if k == item['key']:
                        if k == 'is_native':
                            v = u'显示' if obj.params.get('is_native') else u'不显示'
                        item.update({'value': v})
                        res.update(item)
                if res:
                    params.append(res)
        return params