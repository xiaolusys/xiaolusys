# coding:utf-8
from shopapp.autolist.models import ItemListTask
from shopapp.autolist.forms import ItemListTaskForm
from rest_framework import serializers


class UserIDField(serializers.Field):
    def to_representation(self, obj):
        return obj

    def to_internal_value(self, data):
        request = self.context.get('request', None)
        if not request:
            return None
        session = self.view.request.session
        return session['top_parameters']['visitor_id']


class NickField(serializers.Field):
    def to_representation(self, obj):
        return obj

    def to_internal_value(self, data):
        request = self.context.get('request', None)
        if not request:
            return None
        session = self.view.request.session
        return session['top_parameters']['visitor_nick']


class ItemListTaskSerializer(serializers.ModelSerializer):
    user_id = UserIDField()
    nick = NickField()
    LISTING_TYPE = 'listing'
    DELISTING_TYPE = 'delisting'
    TASK_TYPE = (
        (LISTING_TYPE, u'上架'),
        (DELISTING_TYPE, u'下架'),
        ('recommend', u'下架')
    )
    task_type = serializers.ChoiceField(choices=TASK_TYPE)

    class Meta:
        model = ItemListTask
        #         fields=('nick' ,)
        #         form  = ItemListTaskForm
        fields = ('num_iid', 'user_id', 'nick', 'num', 'task_type')
        # fields=('num_iid' ,'user_id','nick' ,'num'  )

# exclude = ('status',)
