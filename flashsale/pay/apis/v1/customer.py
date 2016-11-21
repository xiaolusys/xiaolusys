# coding=utf-8
from __future__ import absolute_import, unicode_literals

__ALL__ = [
    'get_customer_by_id',
]


def get_customer_by_id(id):
    # type: (int) -> Customer
    from ...models import Customer
    return Customer.objects.get(id=id)
