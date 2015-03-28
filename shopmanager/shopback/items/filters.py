#-*- coding:utf8 -*-
import datetime

from django.db import models
from django.utils.encoding import smart_unicode, force_unicode
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from shopback import paramconfig as pcfg
from shopback.base.options import SimpleListFilter,FieldListFilter
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
        return (('mycharge',u'我接管的'),
                ('uncharge',u'未接管的'),)
    

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        status_name  = self.value()
        myuser_name  = request.user.username
        if not status_name:
            return queryset
        elif status_name == 'mycharge':
            return queryset.filter(models.Q(sale_charger=myuser_name)|models.Q(storage_charger=myuser_name))
                                   
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
        else:       # field is a models.DateField
            today = now.date()
        tomorrow = today + datetime.timedelta(days=1)
        
        self.lookup_kwarg_since = '%s__gte' % field_path
        self.lookup_kwarg_until = '%s__lt' % field_path
        self.links = (
            (_('All'), {}),
            (_(u'未来七天'), {
                self.lookup_kwarg_since: str(today + datetime.timedelta(days=1)),
                self.lookup_kwarg_until: str(today + datetime.timedelta(days=8)),
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
                self.lookup_kwarg_until: str(today ),
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
        