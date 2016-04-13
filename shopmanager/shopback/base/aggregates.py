from django.conf import settings
from django.db.models import Aggregate
from django.db.models.sql.aggregates import Aggregate as AggregateSQL, AggregateField

if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
    ordinal_aggregate_field = AggregateField(
        'DecimalField')  # TODO: this hack prevents mysql backend convert result to float
else:
    ordinal_aggregate_field = AggregateField('TextField')


class ConcatenateSQL(AggregateSQL):
    sql_function = 'GROUP_CONCAT'
    sql_template = '%(function)s(%(distinct)s%(field)s)'

    def __init__(self, col, distinct=False, source=None, **extra):
        super(ConcatenateSQL, self).__init__(col, distinct=distinct and 'DISTINCT ' or '',
                                             source=ordinal_aggregate_field, **extra)


class ConcatSQL(AggregateSQL):
    sql_function = 'CONCAT'
    sql_template = '%(function)s(%(distinct)s%(field)s)'

    def __init__(self, col, distinct=False, source=None, **extra):
        super(ConcatSQL, self).__init__(col, distinct=distinct and 'DISTINCT ' or '', source=ordinal_aggregate_field,
                                        **extra)


class Concatenate(Aggregate):
    name = 'Concatenate'

    def add_to_query(self, query, alias, col, source, is_summary):
        aggregate = ConcatenateSQL(col, is_summary=is_summary)
        query.aggregates[alias] = aggregate


class ConcatenateDistinct(Aggregate):
    name = 'ConcatenateDistinct'

    def add_to_query(self, query, alias, col, source, is_summary):
        aggregate = ConcatenateSQL(col, is_summary=is_summary, distinct=True)
        query.aggregates[alias] = aggregate


class Concat(Aggregate):
    name = 'Concat'

    def add_to_query(self, query, alias, col, source, is_summary):
        aggregate = ConcatSQL(col, is_summary=is_summary)
        query.aggregates[alias] = aggregate
