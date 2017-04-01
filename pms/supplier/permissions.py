# -*- coding:utf8 -*-

def has_sale_supplier_mgr_permission(user):
    return user.is_superuser or user.has_perm('supplier.sale_supplier_mgr')


def has_sale_product_mgr_permission(user):
    return user.is_superuser or user.has_perm('supplier.sale_product_mgr')

