# -*- coding:utf-8 -*-

from rest_framework import permissions
from django.shortcuts import get_object_or_404
from flashsale.pay.models import Customer

class IsOwnerGroup(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if "manage_package_order" in own_perms:
            return True
        else:
            return False
