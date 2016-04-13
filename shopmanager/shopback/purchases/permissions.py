# -*- coding:utf8 -*-

def has_check_purchase_permission(user):
    return user.has_perm('purchases.can_purchase_check')


def has_confirm_purchase_permission(user):
    return user.has_perm('purchases.can_purchase_confirm')


def has_confirm_storage_permission(user):
    return user.has_perm('purchases.can_storage_confirm')


def has_payment_confirm_permission(user):
    return user.has_perm('purchases.can_payment_confirm')
