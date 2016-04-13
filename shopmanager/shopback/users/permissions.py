# -*- coding:utf8 -*-

def has_delete_user_permission(user):
    return user.has_perm('users.has_delete_permission')


def has_download_orderinfo_permission(user):
    return user.has_perm('users.can_download_orderinfo')


def has_download_iteminfo_permission(user):
    return user.has_perm('users.can_download_iteminfo')


def has_manage_itemlist_permission(user):
    return user.has_perm('users.can_manage_itemlist')


def has_recover_instock_permission(user):
    return user.has_perm('users.can_recover_instock')


def has_async_threemtrade_permission(user):
    return user.has_perm('users.can_async_threemtrade')
