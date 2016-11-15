# coding=utf-8
from rest_framework import serializers
from ..models.activity import ActivityEntry, ActivityProduct


class ActivitySerializer(serializers.ModelSerializer):
    is_active_display = serializers.SerializerMethodField()
    login_required_display = serializers.SerializerMethodField()
    act_type_display = serializers.CharField(source='get_act_type_display', read_only=True)
    memo_display = serializers.SerializerMethodField()

    class Meta:
        model = ActivityEntry
        fields = (
            'id',
            'title',
            'schedule_id',
            'act_desc',
            'act_img',
            'act_logo',
            'act_link',
            'mask_link',
            'act_applink',
            'share_icon',
            'share_link',
            'act_type',
            'login_required',
            'start_time',
            'end_time',
            'order_val',
            'extras',
            'is_active',
            'is_active_display',
            'login_required_display',
            'act_type_display',
            'memo_display',
        )

    def get_login_required_display(self, obj):
        # type: (ActivityEntry) -> text_type
        if obj.login_required:
            return u'需要登陆'
        return u'无需登陆'

    def get_is_active_display(self, obj):
        # type: (ActivityEntry) -> text_type
        if obj.is_active:
            return u'已上线'
        return u'未上线'

    def get_memo_display(self, obj):
        # type: (ActivityEntry) -> text_type
        if obj.act_type == ActivityEntry.ACT_TOPIC:  # 专题类型则获取该专题对应排期的供应商名称
            suppliers = obj.get_schedule_suppliers()
            if suppliers:
                return '&'.join([i['supplier_name'] for i in suppliers.values('supplier_name')])
        return ''


class ActivityProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityProduct
        fields = (
            'id',
            'activity',
            'product_id',
            'model_id',
            'product_name',
            'product_img',
            'location_id',
            'pic_type',
            'get_pic_type_display',
            'jump_url',
        )
