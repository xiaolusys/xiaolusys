# coding=utf-8
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from flashsale.pay.models import Customer
from django.contrib.auth.models import Permission


class IsAccessChangeUpperMama(permissions.BasePermission):       #更换/设置/妈妈的上级妈妈
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("xiaolumm.manage_xiaolumama"):
            return True
        else:
            return False