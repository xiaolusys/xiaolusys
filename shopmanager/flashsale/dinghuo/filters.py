# coding=utf-8

from django.contrib.admin import SimpleListFilter
from flashsale.dinghuo.models_user import MyUser, MyGroup


class GroupNameFilter(SimpleListFilter):
    """按组过滤"""
    title = u'采购分组'
    parameter_name = 'groupname'

    def lookups(self, request, model_admin):
        group_list = []
        groups = MyGroup.objects.all()
        for group in groups:
            group_list.append((str(group.id), group.name))
        return tuple(group_list)

    def queryset(self, request, queryset):
        group_id = self.value()
        if not group_id:
            return queryset
        else:
            user_list = MyUser.objects.filter(group_id__in=group_id)
            my_users = [my_user.user.username for my_user in user_list]
            return queryset.filter(buyer_name__in=my_users)