# coding: utf8
from __future__ import absolute_import, unicode_literals

from rest_framework import filters

class ConditionFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        condition = {}
        for k in view.search_fields:
            if type(k) is tuple and k[1] is list:
                v = request.GET.get(k[0])
                if v and v.strip():
                    v = v.strip().split(',')
                if v:
                    condition[k[0]] = v
            else:
                v = request.GET.get(k)
                if v:
                    condition[k] = v
        return queryset.filter(**condition)
