# coding=utf-8
__ALL__ = [
    'get_modelproduct_by_id',
]

from ...models.product import ModelProduct


def get_modelproduct_by_id(id):
    # type: (int) -> ModelProduct
    return ModelProduct.objects.get(id=id)