from rest_framework import permissions
from django.shortcuts import get_object_or_404
from flashsale.pay.models import Customer
from django.contrib.auth.models import Permission



class IsAccessSaleSupplier(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("supplier.manage_sale_supplier"):
            return True
        else:
            return False

class IsAccessSaleCategory(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("supplier.manage_sale_category"):
            return True
        else:
            return False

class IsAccessSaleProduct(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("supplier.manage_sale_product"):
            return True
        else:
            return False

class IsAccessSaleManage(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("supplier.manage_sale_manage"):
            return True
        else:
            return False

class IsAccessSaleManageDetail(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("supplier.manage_sale_manage_detail"):
            return True
        else:
            return False

class IsAccessPreferencePool(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("supplier.manage_preference_pool"):
            return True
        else:
            return False

class IsAccessXiaoluMaMa(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("xiaolumm.manage_xiaolumama"):
            return True
        else:
            return False

class IsAccessAppFullPush(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("protocol.manage_apppushmsg"):
            return True
        else:
            return False

class IsAccessSendBudgetEnvelop(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("pay.manage_user_budget"):
            return True
        else:
            return False

class IsAccessUserCoupon(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("coupon.manage_user_coupon"):
            return True
        else:
            return False

class IsAccessCouponTransferRecord(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("coupon.transfercoupondetail"):
            return True
        else:
            return False