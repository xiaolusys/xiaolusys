# coding=utf-8
from __future__ import unicode_literals, absolute_import

__ALL__ = [
    'get_product_by_id',
]

from shopback.items.models.product import Product


def get_product_by_id(id):
    # type: (int) -> Product
    return Product.objects.filter(id=id).first()



