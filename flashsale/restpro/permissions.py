from rest_framework import permissions
from django.shortcuts import get_object_or_404
from flashsale.pay.models import Customer


class IsOwnerOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Write permissions are only allowed to the owner of the snippet.
        obj_class_name = obj.__class__.__name__
        if obj_class_name in ('SaleTrade', 'SaleRefund', 'ShoppingCart'):
            buyer_id = obj.buyer_id
        elif obj_class_name in ('SaleOrder',):
            buyer_id = obj.sale_trade.buyer_id
        elif obj_class_name in ('UserAddress',):
            buyer_id = obj.cus_uid
        elif obj_class_name in ('Customer',):
            buyer_id = obj.id
        else:
            return True
        try:
            customer = get_object_or_404(Customer, id=buyer_id)
        except:
            return False

        return customer.user == request.user


class IsAdminSuperUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_superuser
