# coding=utf-8
from django.contrib.admin import SimpleListFilter


class Filte_By_Reason(SimpleListFilter):
    title = u"原因"
    parameter_name = "reason"
    r_lit = [(0, u'其他'),
             (1, u'错拍'),
             (2, u'缺货'),
             (3, u'开线/脱色/脱毛/有色差/有虫洞'),
             (4, u'发错货/漏发'),
             (5, u'没有发货'),
             (6, u'未收到货'),
             (7, u'与描述不符'),
             (8, u'退运费'),
             (9, u'发票问题'),
             (10, u'七天无理由')]

    def lookups(self, request, model_admin):
        return tuple(self.r_lit)

    def queryset(self, request, queryset):
        categry = self.value()
        if not categry:
            return queryset
        else:
            qs = queryset.filter(reason__contains=self.r_lit[int(categry)][1])
            return qs
