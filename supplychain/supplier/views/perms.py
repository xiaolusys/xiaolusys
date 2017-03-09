# coding=utf-8
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from flashsale.pay.models import Customer
from django.contrib.auth.models import Permission



class IsAccessSaleSupplier(permissions.BasePermission): #管理供应商

    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("supplier.manage_sale_supplier"):
            return True
        else:
            return False

class IsAccessSaleCategory(permissions.BasePermission):     #管理特卖/选品类目
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("supplier.manage_sale_category"):
            return True
        else:
            return False

class IsAccessSaleProduct(permissions.BasePermission):      #管理特卖/选品列表
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("supplier.manage_sale_product"):
            return True
        else:
            return False

class IsAccessSaleManage(permissions.BasePermission):       #管理排期
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("supplier.manage_sale_manage"):
            return True
        else:
            return False

class IsAccessSaleManageDetail(permissions.BasePermission):     #管理排期明细
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("supplier.manage_sale_manage_detail"):
            return True
        else:
            return False

class IsAccessPreferencePool(permissions.BasePermission):       #管理特卖/产品资料参数表
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("supplier.manage_preference_pool"):
            return True
        else:
            return False

# class IsAccessChangeUpperMama(permissions.BasePermission):       #更换/设置/妈妈的上级妈妈
#     def has_permission(self, request, view):
#         user = request.user
#         own_perms = user.get_group_permissions()
#         if user.has_perm("xiaolumm.manage_change_uppermama"):
#             return True
#         else:
#             return False
class IsAccessAppFullPush(permissions.BasePermission):      #管理消息推送
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("protocol.manage_apppushmsg"):
            return True
        else:
            return False

# class IsAccessAppFullPush(permissions.BasePermission):      #管理消息推送
#     def has_permission(self, request, view):
#         user = request.user
#         own_perms = user.get_group_permissions()
#         if user.has_perm("protocol.manage_apppushmsg"):
#             return True
#         else:
#             return False

# class IsAccessSendBudgetEnvelop(permissions.BasePermission):        #管理发送红包: 创建用户budget_log记录
#     def has_permission(self, request, view):
#         user = request.user
#         own_perms = user.get_group_permissions()
#         if user.has_perm("pay.manage_user_budget"):
#             return True
#         else:
#             return False

# class IsAccessUserCoupon(permissions.BasePermission):           #管理特卖/优惠券/用户优惠券表
#     def has_permission(self, request, view):
#         user = request.user
#         own_perms = user.get_group_permissions()
#         if user.has_perm("coupon.manage_user_coupon"):
#             return True
#         else:
#             return False
#
# class IsAccessCouponTransferRecord(permissions.BasePermission):     #管理特卖/精品券流通记录
#     def has_permission(self, request, view):
#         user = request.user
#         own_perms = user.get_group_permissions()
#         if user.has_perm("coupon.manage_transfer_coupondetail"):
#             return True
#         else:
#             return False

# class IsAccessNinePicAdver(permissions.BasePermission):         #设置9张图
#     def has_permission(self, request, view):
#         user = request.user
#         own_perms = user.get_group_permissions()
#         if user.has_perm("xiaolumm.manage_ninepicadver"):
#             return True
#         else:
#             return False


# class IsAccessMallActivity(permissions.BasePermission):             #管理商城活动
#     def has_permission(self, request, view):
#         user = request.user
#         own_perms = user.get_group_permissions()
#         if user.has_perm("pay.manage_mall_activity"):
#             return True
#         else:
#             return False


