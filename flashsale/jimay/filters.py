# coding: utf8
from __future__ import absolute_import, unicode_literals

import sys
from django.contrib.admin.options import IncorrectLookupParameters
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils.encoding import smart_unicode, smart_text
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import SimpleListFilter, FieldListFilter

from .models import JimayAgentStat

class AgentInviteCountFieldListFilter(FieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg_gte = '%s__gte' % field_path
        self.lookup_kwarg_lt = '%s__lte' % field_path
        gte = request.GET.get(self.lookup_kwarg_gte)
        lte  = request.GET.get(self.lookup_kwarg_lt)
        self.lookup_kwarg_gte_val = gte and gte.isdigit() and float(gte)
        if lte and lte.lower() == 'inf':
            lte = str(sys.maxint)
        self.lookup_kwarg_lte_val = lte and lte.isdigit() and float(lte)
        field.verbose_name = '邀请人数区间'
        super(AgentInviteCountFieldListFilter, self).__init__(
            field, request, params, model, model_admin, field_path)

    def expected_parameters(self):
        return [self.lookup_kwarg_gte, self.lookup_kwarg_lt]

    def queryset(self, request, queryset):
        if not (self.lookup_kwarg_gte_val and self.lookup_kwarg_lte_val):
            return queryset
        agent_ids = list(JimayAgentStat.objects.filter(
            direct_invite_num__gte=self.lookup_kwarg_gte_val,
            direct_invite_num__lte=self.lookup_kwarg_lte_val,
        ).values_list('agent', flat=True))
        try:
            return queryset.filter(id__in=agent_ids)
        except ValidationError as e:
            raise IncorrectLookupParameters(e)

    def choices(self, changelist):
        yield {
            'selected': self.lookup_kwarg_gte_val is None,
            'query_string': changelist.get_query_string(
                    {}, [self.lookup_kwarg_gte, self.lookup_kwarg_lt]
                ),
            'display': _('All')
        }
        count_ranges =(
            (1, 9),
            (10, 19),
            (20, 29),
            (30, 39),
            (40, 49),
            (50, 59),
            (60, 'Inf'),
        )

        for lookup in count_ranges:
            title = '%s ~ %s' % lookup
            yield {
                'selected': smart_text(lookup[0]) == self.lookup_kwarg_gte_val
                            and smart_text(lookup[1]) == self.lookup_kwarg_lte_val,
                'query_string': changelist.get_query_string(
                    {self.lookup_kwarg_gte: lookup[0], self.lookup_kwarg_lt: lookup[1]},
                    [self.lookup_kwarg_gte, self.lookup_kwarg_lt]
                ),
                'display': title,
            }


FieldListFilter.register(lambda f: bool(f.choices), AgentInviteCountFieldListFilter)

