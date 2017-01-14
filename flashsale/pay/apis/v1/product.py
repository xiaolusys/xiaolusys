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

def get_virtual_modelproduct_from_boutique_modelproduct(modelid):
    """从售卖商品的modelid找到虚拟商品券modelproduct
    """
    model_product = ModelProduct.objects.filter(id=modelid, is_boutique=True).first()
    if not model_product:
        return None

    payinfo = model_product.extras.get('payinfo')
    if not payinfo:
        return None
    coupon_template_ids = payinfo.get('coupon_template_ids')
    if not coupon_template_ids:
        return None

    templateid = coupon_template_ids[0]
    virtual_model_products = ModelProduct.objects.get_virtual_modelproducts()  # 虚拟商品
    find_mp = None
    for md in virtual_model_products:
        md_bind_tpl_id = md.extras.get('template_id')
        if not md_bind_tpl_id:
            continue
        if templateid == md_bind_tpl_id:
            find_mp = md
            break
    return find_mp
