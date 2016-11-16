# coding=utf-8
__author__ = 'yan.huang'
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from flashsale.pay.models import Customer


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    自定义权限只允许一个对象的所有者来编辑它
    """

    def has_object_permission(self, request, view, obj):

        # 允许任何请求读取权限
        # so we'll always allow GET, HEAD or OPTIONS requests.
        buyer_id = None
        if hasattr(obj, 'buyer_id'):
            buyer_id = obj.buyer_id
        elif hasattr(obj, 'cus_uid'):
            buyer_id = obj.cus_uid

        try:
            customer = get_object_or_404(Customer, id=buyer_id)
        except:
            return False

        return customer.user == request.user


class IsAdminSuperUser(permissions.BasePermission):
    # 允许访问仅为管理员用户。
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser
