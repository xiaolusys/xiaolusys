# -*- coding:utf8 -*-
import datetime

from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from bitfield.admin import BitFieldListFilter
from django.contrib.admin import SimpleListFilter, FieldListFilter


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
            (_(u'今日'), {
                self.lookup_kwarg_since: str(today),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_(u'明日'), {
                self.lookup_kwarg_since: str(tomorrow),
                self.lookup_kwarg_until: str(today + datetime.timedelta(days=2)),
            }),
            (_(u'后天'), {
                self.lookup_kwarg_since: str(today + datetime.timedelta(days=2)),
                self.lookup_kwarg_until: str(today + datetime.timedelta(days=3)),
            }),
            (_(u'未来七天'), {
                self.lookup_kwarg_since: str(today + datetime.timedelta(days=1)),
                self.lookup_kwarg_until: str(today + datetime.timedelta(days=8)),
            }),
            (_(u'未来两周'), {
                self.lookup_kwarg_since: str(today + datetime.timedelta(days=1)),
                self.lookup_kwarg_until: str(today + datetime.timedelta(days=16)),
            }),
            (_(u'未来一月'), {
                self.lookup_kwarg_since: str(today + datetime.timedelta(days=1)),
                self.lookup_kwarg_until: str(today + datetime.timedelta(days=31)),
            }),
            (_(u'未来两月'), {
                self.lookup_kwarg_since: str(today + datetime.timedelta(days=1)),
                self.lookup_kwarg_until: str(today + datetime.timedelta(days=61)),
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
            (_(u'过去一月'), {
                self.lookup_kwarg_since: str(
                    datetime.date(last_month and today.year or today.year - 1, last_month or 12, 1)),
                self.lookup_kwarg_until: str(datetime.date(today.year, today.month, 1)),
            }),
            (_(u'本年'), {
                self.lookup_kwarg_since: str(today.replace(month=1, day=1)),
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


FieldListFilter.register(
    lambda f: isinstance(f, models.DateField), DateFieldListFilter)
