# -*- coding:utf8 -*-
import datetime
from django.db import models
from django.db.models import F
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from core.filters import SimpleListFilter, FieldListFilter
from shopback.items.models import SkuStock
from shopback.items.models import Product


class ChargerFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    title = u'接管状态'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'charger'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (('mycharge', u'我接管的'),
                ('uncharge', u'未接管的'),)

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        status_name = self.value()
        myuser_name = request.user.username
        if not status_name:
            return queryset
        elif status_name == 'mycharge':
            return queryset.filter(models.Q(sale_charger=myuser_name) | models.Q(storage_charger=myuser_name))

        else:
            return queryset.exclude(sale_charger=myuser_name).exclude(storage_charger=myuser_name)


class DateScheduleFilter(FieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.field_generic = '%s__' % field_path
        self.date_params = dict([(k, v) for k, v in params.items()
                                 if k.startswith(self.field_generic)])

        now = timezone.now()
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        if now.tzinfo is not None:
            current_tz = timezone.get_current_timezone()
            now = now.astimezone(current_tz)
            if hasattr(current_tz, 'normalize'):
                # available for pytz time zones
                now = current_tz.normalize(now)

        if isinstance(field, models.DateTimeField):
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # field is a models.DateField
            today = now.date()
        tomorrow = today + datetime.timedelta(days=1)

        self.lookup_kwarg_since = '%s__gte' % field_path
        self.lookup_kwarg_until = '%s__lt' % field_path
        self.links = (
            (_('All'), {}),
            (_(u'五天后'), {
                self.lookup_kwarg_since: str(today + datetime.timedelta(days=5)),
                self.lookup_kwarg_until: str(today + datetime.timedelta(days=6)),
            }),
            (_(u'四天后'), {
                self.lookup_kwarg_since: str(today + datetime.timedelta(days=4)),
                self.lookup_kwarg_until: str(today + datetime.timedelta(days=5)),
            }),
            (_(u'大后天'), {
                self.lookup_kwarg_since: str(today + datetime.timedelta(days=3)),
                self.lookup_kwarg_until: str(today + datetime.timedelta(days=4)),
            }),
            (_(u'后天'), {
                self.lookup_kwarg_since: str(today + datetime.timedelta(days=2)),
                self.lookup_kwarg_until: str(today + datetime.timedelta(days=3)),
            }),
            (_(u'明日'), {
                self.lookup_kwarg_since: str(tomorrow),
                self.lookup_kwarg_until: str(today + datetime.timedelta(days=2)),
            }),
            (_(u'今日'), {
                self.lookup_kwarg_since: str(today),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_(u'昨天'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=1)),
                self.lookup_kwarg_until: str(today),
            }),
            (_(u'前天'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=2)),
                self.lookup_kwarg_until: str(today - datetime.timedelta(days=1)),
            }),
            (_(u'三天前'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=3)),
                self.lookup_kwarg_until: str(today - datetime.timedelta(days=2)),
            }),
            (_(u'四天前'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=4)),
                self.lookup_kwarg_until: str(today - datetime.timedelta(days=3)),
            }),
            (_(u'五天前'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=5)),
                self.lookup_kwarg_until: str(today - datetime.timedelta(days=4)),
            }),
            (_(u'六天前'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=6)),
                self.lookup_kwarg_until: str(today - datetime.timedelta(days=5)),
            }),
            (_(u'七天前'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=7)),
                self.lookup_kwarg_until: str(today - datetime.timedelta(days=6)),
            }),
        )
        super(DateScheduleFilter, self).__init__(
            field, request, params, model, model_admin, field_path)

    def expected_parameters(self):
        return [self.lookup_kwarg_since, self.lookup_kwarg_until]

    def choices(self, cl):
        for title, param_dict in self.links:
            yield {
                'selected': self.date_params == param_dict,
                'query_string': cl.get_query_string(
                    param_dict, [self.field_generic]),
                'display': title,
            }


FieldListFilter.register(
    lambda f: isinstance(f, models.DateField), DateScheduleFilter)

from flashsale.dinghuo.models_user import MyUser, MyGroup


class GroupNameFilter(SimpleListFilter):
    """"""
    title = u'采购分组'
    parameter_name = 'groupname'

    def lookups(self, request, model_admin):
        group_list = []
        groups = MyGroup.objects.all()
        for group in groups:
            group_list.append((str(group.id), group.name))
        return tuple(group_list)

    def queryset(self, request, queryset):
        group_id = self.value()
        if not group_id:
            return queryset
        else:
            user_list = MyUser.objects.filter(group_id__in=group_id)
            my_users = [my_user.user.username for my_user in user_list]
            return queryset.filter(sale_charger__in=my_users)


from shopback.categorys.models import ProductCategory


class CategoryFilter(SimpleListFilter):
    """ """
    title = u'商品类别'
    parameter_name = 'category'

    def lookups(self, request, model_admin):

        cat_id = request.GET.get(self.parameter_name, '')
        cat_parent_id = None
        try:
            cat_parent_id = ProductCategory.objects.get(cid=cat_id).parent_cid
        except:
            pass

        cate_list = []
        cate_qs = ProductCategory.objects.filter(is_parent=True, status=ProductCategory.NORMAL)
        for cate in cate_qs:
            cate_list.append((str(cate.cid), str(cate)))
            if cat_id and int(cat_id) == cate.cid or (cat_parent_id and int(cat_parent_id) == cate.cid):
                sub_cates = ProductCategory.objects.filter(parent_cid=cate.cid, is_parent=False,
                                                           status=ProductCategory.NORMAL)
                for sub_cate in sub_cates:
                    cate_list.append((str(sub_cate.cid), str(sub_cate)))

        return tuple(cate_list)

    def queryset(self, request, queryset):

        cat_id = self.value()
        if not cat_id:
            return queryset
        else:
            categorys = ProductCategory.objects.filter(parent_cid=cat_id)
            cate_ids = [cate.cid for cate in categorys]
            if len(cate_ids) == 0:
                return queryset.filter(category=cat_id)
            else:
                cate_ids.append(int(cat_id))
                return queryset.filter(category__in=cate_ids)


class ProductSkuStatsUnusedStockFilter(SimpleListFilter):
    """按冗余库存数过滤"""
    title = u'冗余库存数'
    parameter_name = 'unused_stock_cnt'

    def lookups(self, request, model_admin):
        condition = (("3", u'大于0且可退货'),
                     ("1", u'大于0'),
                     ("2", u'等于0'))
        return condition

    def queryset(self, request, queryset):
        status_id = self.value()
        if not status_id:
            return queryset
        else:
            if status_id == '1':
                return queryset.filter(return_quantity__gt=F('sold_num') + F('rg_quantity')
                                                           - F('history_quantity') - F('adjust_quantity') - F(
                    'inbound_quantity'))
            if status_id == '2':
                return queryset.filter(return_quantity=F('sold_num') + F('rg_quantity')
                                                       - F('history_quantity') - F('adjust_quantity') - F(
                    'inbound_quantity'))
            if status_id == '3':
                return queryset.filter(id__in=SkuStock.redundancies())


class ProductTypeFilter(SimpleListFilter):
    """按是否虚拟商品过滤"""
    title = u'商品类型'
    parameter_name = 'product_type'

    def lookups(self, request, model_admin):
        condition = (("0", u'普通商品'),
                     ("1", u'虚拟商品'),
                     ("2", u'非卖品'))
        return condition

    def queryset(self, request, queryset):
        status_id = self.value()
        if not status_id:
            return queryset
        else:
            if status_id == '0':
                return queryset.filter(product__type=0)
            if status_id == '1':
                return queryset.filter(product__type=1)
            if status_id == '2':
                return queryset.filter(product__type=2)


class ProductWareByFilter(SimpleListFilter):
    """按是否虚拟商品过滤"""
    title = u'发货仓'
    parameter_name = 'ware_by'

    def lookups(self, request, model_admin):
        condition = (("1", u'上海仓'),
                     ("2", u'广州仓'),
                     ("9", u'第三方仓'))
        return condition

    def queryset(self, request, queryset):
        status_id = self.value()
        if not status_id:
            return queryset
        else:
            return queryset.filter(product__ware_by=int(status_id))


class ProductStatusFilter(SimpleListFilter):
    """按商品状态过滤"""
    title = u'商品状态'
    parameter_name = 'product_status'

    def lookups(self, request, model_admin):
        condition = (("1", u'正常'),
                     ("2", u'保留'),
                     ("3", u'作废'))
        return condition

    def queryset(self, request, queryset):
        status_id = self.value()
        if not status_id:
            return queryset
        else:
            if status_id == '1':
                return queryset.filter(product__status=Product.NORMAL)
            if status_id == '2':
                return queryset.filter(product__status=Product.REMAIN)
            if status_id == '3':
                return queryset.filter(product__status=Product.REMAIN)


class ProductCategoryFilter(SimpleListFilter):
    """按商品状态过滤"""
    title = u'商品类别'
    parameter_name = 'product_category'

    @property
    def product_category(self):
        if not hasattr(self, '_product_category_'):
            self._product_category_ = ProductCategory.objects.filter(status=ProductCategory.NORMAL)
        return self._product_category_

    def lookups(self, request, model_admin):
        return [(p.cid, p.name) for p in ProductCategory.objects.filter(status=ProductCategory.NORMAL)] + [
            (-1, u'非优尼世界')]

    def queryset(self, request, queryset):
        sid = self.value()
        if not sid:
            return queryset
        elif sid == '-1':
            pid = ProductCategory.objects.get(name=u'优尼世界').cid
            return queryset.exclude(product__category_id=pid)
        else:
            return queryset.filter(product__category_id=sid)


class ProductSkuStatsSupplierIdFilter(SimpleListFilter):
    """按订货单状态过滤"""
    title = u'供应商ID'
    parameter_name = 'supplier_id'

    def lookups(self, request, model_admin):
        condition = (("3", u'大于0且可退货'),
                     ("1", u'大于0'),
                     ("2", u'等于0'))
        return condition

    def queryset(self, request, queryset):
        supplier_id = self.value()
        from shopback.items.models import SkuStock
        from supplychain.supplier.models import SaleSupplier
        supplier = SaleSupplier.objects.filter(pk=supplier_id).first() if supplier_id else None
        if not supplier:
            return queryset
        else:
            return queryset.filter(product_id__in=SkuStock.filter_by_supplier(supplier.id))


class ProductSkuStatsSupplierNameFilter(SimpleListFilter):
    """按订货单状态过滤"""
    title = u'供应商名称'
    parameter_name = 'supplier_name'

    def lookups(self, request, model_admin):
        condition = (("3", u'大于0且可退货'),
                     ("1", u'大于0'),
                     ("2", u'等于0'))
        return condition

    def queryset(self, request, queryset):
        supplier_name = self.value()
        from shopback.items.models import SkuStock
        from supplychain.supplier.models import SaleSupplier
        supplier = SaleSupplier.objects.filter(supplier_name=supplier_name).first() if supplier_name else None
        if not supplier:
            return queryset
        else:
            return queryset.filter(product_id__in=SkuStock.filter_by_supplier(supplier.id))
