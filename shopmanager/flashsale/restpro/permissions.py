from rest_framework import permissions
from django.shortcuts import get_object_or_404
from flashsale.pay.models_user import Customer

class SaleTradeOwnerOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):

        # Write permissions are only allowed to the owner of the snippet.
        try:
            customer = get_object_or_404(Customer,id=obj.buyer_id)
        except:
            return False
        
        return customer.user == request.user