# coding=utf-8
from flashsale.dinghuo.models_user import MyUser, MyGroup
from django.db import models
from django.db.models import Count, Q
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.admin import SimpleListFilter, FieldListFilter
from django.contrib.auth.models import User, Group
import datetime
from flashsale.dinghuo.models import OrderList


class GroupNameFilter(SimpleListFilter):
    """按组过滤"""
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
            return queryset.filter(buyer_name__in=my_users)


class InBoundCreatorFilter(SimpleListFilter):
    title = u'创建者'
    parameter_name = u'creator_name'

    def lookups(self, request, model_admin):
        from flashsale.dinghuo.models import InBound
        from flashsale.dinghuo.views import InBoundViewSet
        user_ids = [x['creator'] for x in InBound.objects.all().values('creator').distinct()]

        tmp = []
        for user in User.objects.filter(id__in=user_ids).order_by('id'):
            tmp.append((user.id, InBoundViewSet.get_username(user)))
        return tmp

    def queryset(self, request, queryset):
        user_id = self.value()
        if not user_id:
            return queryset
        else:
            return queryset.filter(creator_id=user_id)


class OrderListStatusFilter(SimpleListFilter):
    """按订货单状态过滤"""
    title = u'订货单状态'
    parameter_name = 'custom_status'

    def lookups(self, request, model_admin):
        status_list = OrderList.ORDER_PRODUCT_STATUS
        querstion = (("0", u'售后处理'),)
        status_list1 = status_list + querstion
        return status_list1

    def queryset(self, request, queryset):
        status_id = self.value()
        if not status_id:
            return queryset
        else:
            if status_id == '0':
                return queryset.filter(status__in=(OrderList.QUESTION, OrderList.CIPIN, OrderList.QUESTION_OF_QUANTITY))
            else:
                return queryset.filter(status=status_id)


class OrderListReceiveStatusFilter(SimpleListFilter):
    """按订货单状态过滤"""
    title = u'到货处理<重复待删>'
    parameter_name = 'receive_status'

    def lookups(self, request, model_admin):
        status_list1 = (("0", u'未到货'),
                        ("1", u'缺货'),
                        ("2", u'有次品'),
                        ("3", u'次品又缺货'),
                        ("4", u'完成'),
                        ("5", u'需售后'),
                        )
        return status_list1

    def queryset(self, request, queryset):
        status_id = self.value()
        if not status_id:
            return queryset
        else:
            if status_id == '0':
                return queryset.filter(lack=None)
            elif status_id == '1':
                return queryset.filter(lack=True)
            elif status_id == '2':
                return queryset.filter(inferior=True)
            elif status_id == '3':
                return queryset.filter(inferior=True, lack=True)
            elif status_id == '4':
                return queryset.filter(lack=False)
            elif status_id == '5':
                return queryset.filter(Q(inferior=True) | Q(lack=True))


class OrderListStatusFilter2(SimpleListFilter):
    title = u'订货单状态'
    parameter_name = 'orderlist_status'

    def lookups(self, request, model_admin):
        return OrderList.ORDER_PRODUCT_STATUS + (('待处理', u'待处理'),)

    def queryset(self, request, queryset):
        status_id = self.value()
        if not status_id:
            return queryset
        else:
            if status_id == u'待处理':
                return queryset.exclude(orderlist__status__in=[OrderList.COMPLETED, OrderList.ZUOFEI])
            else:
                return queryset.filter(orderlist__status=status_id)


class DateFieldListFilter(FieldListFilter):
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
        yesterday = today - datetime.timedelta(days=1)
        before_yesterday = today - datetime.timedelta(days=2)
        tomorrow = today + datetime.timedelta(days=1)
        last_month = today.month - 1

        self.lookup_kwarg_since = '%s__gte' % field_path
        self.lookup_kwarg_until = '%s__lt' % field_path
        self.links = (
            (_('All'), {}),
            (_(u'本周'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=today.weekday())),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_(u'上周'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=today.weekday() + 7)),
                self.lookup_kwarg_until: str(today - datetime.timedelta(days=today.weekday())),
            }),
            (_(u'今日'), {
                self.lookup_kwarg_since: str(today),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_(u'昨日'), {
                self.lookup_kwarg_since: str(yesterday),
                self.lookup_kwarg_until: str(today),
            }),
            (_(u'前日'), {
                self.lookup_kwarg_since: str(before_yesterday),
                self.lookup_kwarg_until: str(yesterday),
            }),
            (_(u'过去七天'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=7)),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_(u'本月'), {
                self.lookup_kwarg_since: str(today.replace(day=1)),
                self.lookup_kwarg_until: str(tomorrow),
            }),
        )
        super(DateFieldListFilter, self).__init__(
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


class BuyerNameFilter(SimpleListFilter):
    title = u'负责人'
    parameter_name = 'buyer_id'

    def lookups(self, request, model_admin):
        buyer_role = Group.objects.get(name=u"小鹿订货员")
        options = []
        for user in buyer_role.user_set.all():
            name = '%s%s' % (user.last_name, user.first_name) or user.username
            options.append((user.id, name))
        options.append((0, u'空缺'))
        return options
        # buyer_ids = []
        #
        # for row in OrderList.objects.only('buyer').values('buyer').annotate(Count('id')):
        #     if not row.get('buyer'):
        #         continue
        #     buyer_ids.append(row['buyer'])
        # options = []
        #
        # for user in User.objects.filter(id__in=buyer_ids).order_by('id'):
        #     name = '%s%s' % (user.last_name, user.first_name) or user.username
        #     options.append((user.id, name))
        # options.append((0, '空缺'))
        # return options

    def queryset(self, request, queryset):
        if self.value() == None:
            return queryset
        buyer_id = int(self.value())
        return queryset.filter(buyer_id=buyer_id)

class CreaterFilter(SimpleListFilter):
    title = u'负责人'
    parameter_name = 'buyer_id'

    def lookups(self, request, model_admin):
        buyer_role = Group.objects.get(name=u"小鹿订货员")
        options = []
        for user in buyer_role.user_set.all():
            name = '%s%s' % (user.last_name, user.first_name) or user.username
            options.append((user.id, name))
        options.append((0, u'空缺'))
        return options
        # buyer_ids = []
        #
        # for row in OrderList.objects.only('buyer').values('buyer').annotate(Count('id')):
        #     if not row.get('buyer'):
        #         continue
        #     buyer_ids.append(row['buyer'])
        # options = []
        #
        # for user in User.objects.filter(id__in=buyer_ids).order_by('id'):
        #     name = '%s%s' % (user.last_name, user.first_name) or user.username
        #     options.append((user.id, name))
        # options.append((0, '空缺'))
        # return options

    def queryset(self, request, queryset):
        if self.value() == None:
            return queryset
        buyer_id = int(self.value())
        return queryset.filter(creater=buyer_id)