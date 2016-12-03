# coding=utf-8
from __future__ import absolute_import, unicode_literals

__ALL__ = [
    'get_customer_by_id',
]


def get_customer_by_id(id):
    # type: (int) -> Customer
    from ...models import Customer

    return Customer.objects.get(id=id)


def get_customer_by_unionid(unionid):
    # type: (text_type) ->Optional[Customer]
    from ...models import Customer
    return Customer.objects.filter(unionid=unionid, status=Customer.NORMAL).first()
