# coding=utf-8
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from flashsale.pay.models import Customer
from django.contrib.auth.models import Permission

class IsAccessNinePicAdver(permissions.BasePermission):         #设置9张图
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("xiaolumm.manage_ninepicadver"):
            return True
        else:
            return False