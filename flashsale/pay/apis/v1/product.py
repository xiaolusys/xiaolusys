# coding=utf-8
from __future__ import unicode_literals, absolute_import

__ALL__ = [
    'get_modelproduct_by_id',
    'get_virtual_modelproducts',
]

from ...models.product import ModelProduct


def get_modelproduct_by_id(id):
    # type: (int) -> ModelProduct
    return ModelProduct.objects.get(id=id)


def get_virtual_modelproducts():
    # type: () -> Optional[List[ModelProduct]]
    """获取虚拟款式列表记录,boutique coupon
    """
    return ModelProduct.objects.get_virtual_modelproducts()


def get_is_onsale_modelproducts():
    # type: () -> Optional[List[ModelProduct]]
    """获取特卖秒杀商品
    """
    return ModelProduct.objects.get_is_onsale_modelproducts()

def get_boutique_goods():
    # type: () -> Optional[List[ModelProduct]]
    """获取boutique商品
    """
    return ModelProduct.objects.get_boutique_goods()
