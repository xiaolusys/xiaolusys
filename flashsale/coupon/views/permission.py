# coding=utf-8
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from flashsale.pay.models import Customer
from django.contrib.auth.models import Permission


class IsAccessUserCoupon(permissions.BasePermission):           #发放 赠送精品券
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("coupon.manage_user_coupon"):
            return True
        else:
            return False

class IsAccessCouponTransferRecord(permissions.BasePermission):     #赠送精品券积分
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("coupon.manage_transfer_coupondetail"):
            return True
        else:
            return False