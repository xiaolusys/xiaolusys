# -*- coding:utf8 -*-

def has_change_product_skunum_permission(user):
    return user.is_superuser or user.has_perm('items.change_product_skunum')
