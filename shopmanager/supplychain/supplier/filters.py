# -*- coding:utf8 -*-
import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.admin import FieldListFilter


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
            (_(u'七天后'), {
                self.lookup_kwarg_since: str(today + datetime.timedelta(days=7)),
                self.lookup_kwarg_until: str(today + datetime.timedelta(days=8)),
            }),
            (_(u'六天后'), {
                self.lookup_kwarg_since: str(today + datetime.timedelta(days=6)),
                self.lookup_kwarg_until: str(today + datetime.timedelta(days=7)),
            }),
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

from django.contrib.admin.filters import SimpleListFilter
from .models import SaleCategory, SaleProduct


class CategoryFilter(SimpleListFilter):
    """ """
    title = u'商品类别'
    parameter_name = 'category'

    def lookups(self, request, model_admin):

        cat_id = request.GET.get(self.parameter_name, '')
        cat_parent_id = None
        try:
            cat_parent_id = SaleCategory.objects.get(cid=cat_id).parent_cid
        except:
            pass

        cate_list = []
        cate_qs = SaleCategory.objects.filter(is_parent=True, status=SaleCategory.NORMAL)
        for cate in cate_qs:
            cate_list.append((str(cate.cid), str(cate)))
            if cat_id and cat_id == cate.cid or ( cat_parent_id and cat_parent_id == cate.cid):
                sub_cates = SaleCategory.objects.filter(parent_cid=cate.cid, status=SaleCategory.NORMAL)
                for sub_cate in sub_cates:
                    cate_list.append((str(sub_cate.cid), str(sub_cate)))

        return tuple(cate_list)

    def queryset(self, request, queryset):
        cat_id = self.value()
        if not cat_id:
            return queryset
        try:
            return queryset.filter(sale_category__cid__startswith=cat_id)
        except:
            return queryset.filter(category__cid__startswith=cat_id)


from .models import BuyerGroup
from django.contrib.auth.models import User


class BuyerGroupFilter(SimpleListFilter):
    title = u'买手组'
    parameter_name = 'group'

    def lookups(self, request, model_admin):
        return tuple([(1, u'A组'), (2, u'B组'), (3, u'C组')])

    def queryset(self, request, queryset):
        group_id = self.value()
        if group_id is None:
            return queryset
        else:
            buyers = BuyerGroup.objects.values("buyer_name").filter(buyer_group=group_id)
            buyer_list = [val['buyer_name'] for val in buyers]
            users = User.objects.filter(username__in=buyer_list)
            syd_id_list = [val.id for val in users]
            queryset_group = queryset.filter(contactor__in=syd_id_list)
            return queryset_group


from .models import SupplierZone


class SupplierZoneFilter(SimpleListFilter):
    title = u'片区'
    parameter_name = 'supplier_zone'

    def lookups(self, request, model_admin):
        zones = SupplierZone.objects.all()
        zone_list = []
        for zone in zones:
            zone_list.append((zone.id, zone.name))
        return tuple(zone_list)

    def queryset(self, request, queryset):
        supplier_zone = self.value()
        if supplier_zone is None:
            return queryset
        else:
            qs = queryset.filter(supplier_zone=supplier_zone)
            return qs