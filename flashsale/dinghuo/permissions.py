# -*- coding:utf8 -*-


def has_change_order_list_inline_permission(user):
    return user.is_superuser or user.has_perm('dinghuo.change_order_list_inline')
