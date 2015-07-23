# coding=utf-8

from flashsale.dinghuo.models_user import MyUser, MyGroup
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.admin import SimpleListFilter, FieldListFilter
import datetime


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
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=today.weekday()+7)),
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