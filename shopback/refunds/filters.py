# coding=utf-8
from django.contrib.auth.models import User
from django.contrib.admin import SimpleListFilter
import datetime
import calendar


def get_Five_Month(now):
    months_list = []
    # 当前时间的前面5个月
    for i in range(5):
        month = now.month - i
        year = now.year
        if month <= 0:
            year = now.year - 1
            month = 12 - (5 - i) + 1
        months_v = '{0}-{1}'.format(year, month)
        months = (months_v, months_v)
        months_list.append(months)
    return months_list


########################################################################
# 按照月份过滤
class RefundMonthFilter(SimpleListFilter):
    """"""
    title = u'月份'
    parameter_name = 'created_in'

    def lookups(self, request, model_admin):
        now = datetime.datetime.now()
        months_list = get_Five_Month(now)
        return tuple(months_list)

    def queryset(self, request, queryset):
        month_ref = self.value()

        if not month_ref:
            return queryset
        else:
            year, month = month_ref.split('-')
            days = calendar.monthrange(int(year), int(month))[1]
            time_from = datetime.datetime(int(year), int(month), 1, 0, 0, 0)
            time_to = datetime.datetime(int(year), int(month), days, 0, 0, 0)
            return queryset.filter(created__gte=time_from, created__lte=time_to)


from shopback.items.models import Product


def filter_Categry(queryset, categry):
    if categry == '1':
        # 过滤出童装 退货产品
        pros = Product.objects.raw("select id, outer_id from shop_items_product where "
                                   " category_id in (5,12,13,14,15,16,17)   ")
        product_outer_ids = [pro.outer_id for pro in pros]
        qs = queryset.filter(outer_id__in=product_outer_ids)
        return qs

    elif categry == '2':
        # 过滤出女装 退货产品

        pros = Product.objects.raw("select id, outer_id from shop_items_product where "
                                   " category_id in (8,18,19,20,21,22)   ")
        product_outer_ids = [pro.outer_id for pro in pros]
        qs = queryset.filter(outer_id__in=product_outer_ids)
        return qs

    elif categry == '3':
        # 过滤出其他 退货产品
        pros = Product.objects.raw("select id, outer_id from shop_items_product where "
                                   " category_id in (8,18,19,20,21,22,5,12,13,14,15,16,17)   ")
        product_outer_ids = [pro.outer_id for pro in pros]
        qs = queryset.exclude(outer_id__in=product_outer_ids)

        return qs
    else:
        return queryset


# 按照 男童装、 女童装、 女装 过滤  退货商品
class BoyGirlWomen(SimpleListFilter):
    title = u'类别'
    parameter_name = "categery"

    def lookups(self, request, model_admin):
        c_lit = [(1, u'童装'), (2, u'女装'), (3, u'其他')]
        return tuple(c_lit)

    def queryset(self, request, queryset):
        categry = self.value()

        if not categry:
            return queryset
        else:
            queryset_f = filter_Categry(queryset, categry)
            return queryset_f
