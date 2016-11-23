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
    """获取虚拟款式列表记录
    """
    return ModelProduct.objects.get_virtual_modelproducts()
