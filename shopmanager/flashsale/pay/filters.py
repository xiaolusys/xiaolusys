# coding=utf-8
from datetime import datetime, timedelta
from django.contrib.admin import SimpleListFilter
from shopapp.weixin.models_base import WeixinUnionID
from flashsale.xiaolumm.models import XiaoluMama
import constants


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


class CushopProCategoryFiler(SimpleListFilter):
    title = u'类别'
    parameter_name = 'categry'
    r_list = [('t', u'童装'), ('n', u'女装')]

    def lookups(self, request, model_admin):
        return tuple(self.r_list)

    def queryset(self, request, queryset):
        categry = self.value()
        if not categry:
            return queryset
        else:
            if categry == 't':
                fenlei = constants.CHILD_CID_LIST
            elif categry == 'n':
                fenlei = constants.FEMALE_CID_LIST
            else:
                return queryset
            qs = queryset.filter(pro_category__in=fenlei)
            return qs


class MamaCreatedFilter(SimpleListFilter):
    title = u'小鹿妈妈创建时间'
    parameter_name = 'mama_created'

    def lookups(self, request, model_admin):
        return tuple([
            ('1', u'今天'),
            ('2', u'昨天'),
            ('3', u'最近三天'),
            ('7', u'最近七天'),
        ])

    def queryset(self, request, queryset):
        delta = request.GET.get('mama_created')

        if not delta:
            return queryset
        else:
            delta = int(delta) - 1

        today = datetime.now()
        start_date = datetime(today.year, today.month, today.day) - timedelta(days=delta)
        mamas = XiaoluMama.objects.filter(created__gte=start_date).values('openid')
        openids = WeixinUnionID.objects.filter(unionid__in=[x['openid'] for x in mamas]).values('openid')

        return queryset.filter(recipient__in=openids)
