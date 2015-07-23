from rest_framework import permissions
from django.shortcuts import get_object_or_404
from flashsale.pay.models_user import Customer

class IsOwnerOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        
        # Write permissions are only allowed to the owner of the snippet.
        buyer_id = None
        if hasattr(obj,'buyer_id'):
            buyer_id = obj.buyer_id
        elif hasattr(obj,'cus_uid'):
            buyer_id = obj.cus_uid

        try:
            customer = get_object_or_404(Customer,id=buyer_id)
        except:
            return False
        
        return customer.user == request.user
    
class IsAdminSuperUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_superuser