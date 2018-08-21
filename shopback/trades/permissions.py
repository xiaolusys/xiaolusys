# -*- coding:utf8 -*-

def has_delete_trade_permission(user):
    return user.has_perm('trades.has_delete_permission')


def has_check_order_permission(user):
    return user.has_perm('trades.can_trade_aduit')


def has_modify_trade_permission(user):
    return user.has_perm('trades.can_trade_modify')


def has_sync_post_permission(user):
    return user.has_perm('trades.sync_trade_post_taobao')


def has_merge_order_permission(user):
    return user.has_perm('trades.merge_order_action')


def has_pull_order_permission(user):
    return user.has_perm('trades.pull_order_action')


def has_unlock_trade_permission(user):
    return user.has_perm('trades.unlock_trade_action')


def has_invalid_order_permission(user):
    return user.has_perm('trades.invalid_order_action')


def has_export_logistic_permission(user):
    return user.has_perm('trades.export_logistic_action')


def has_export_buyer_permission(user):
    return user.has_perm('trades.export_buyer_action')


def has_export_finance_permission(user):
    return user.has_perm('trades.export_finance_action')


def has_export_orderdetail_permission(user):
    return user.has_perm('trades.export_orderdetail_action')


def has_export_yunda_permission(user):
    return user.has_perm('trades.export_yunda_action')
