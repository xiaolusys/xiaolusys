# coding=utf-8
"""
    自定义的权限尽量在此记录
"""
permission_trades = [
    ('manage_package_order', ('trades', 'packageorder'), 'manage package order', u'管理包裹')
]

permissions = []
permissions.append(permission_trades)


def update_permissions():
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    for permission in permissions:
        content_id = ContentType.objects.get(app_label=permissions[0], model=permissions[1]).id
        Permission.get_or_create(name=permission[2], content_type=content_id, codename=permission[0])
# 获取权限对应的model
# from django.apps import apps
# apps.get_models('trades', 'packageorder')
