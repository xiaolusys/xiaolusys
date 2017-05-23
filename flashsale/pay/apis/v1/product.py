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
    from flashsale.coupon.apis.v1.coupontemplate import get_boutique_coupon_modelid_by_templateid
    find_mp_id = get_boutique_coupon_modelid_by_templateid(templateid)
    find_mp = ModelProduct.objects.filter(id=find_mp_id).first()  # 虚拟商品
    # find_mp = None
    # for md in virtual_model_products:
    #     md_bind_tpl_id = md.extras.get('template_id')
    #     if not md_bind_tpl_id:
    #         continue
    #     if templateid == md_bind_tpl_id:
    #         find_mp = md
    #         break
    return find_mp

def get_level_differential_from_coupon_modelproduct(model_product, lowest_agent_price):
    """从coupon商品的modelid找到虚拟商品券的差价
    """
    result = []
    if model_product:
        all_price = []
        if len(model_product.products) == 5:
            for product in model_product.products:
                all_price.append(product.agent_price)
        elif len(model_product.products) == 1 and len(model_product.products[0].eskus) == 5:
            for sku in model_product.products[0].eskus:
                all_price.append(sku.agent_price)
        all_price.sort(reverse=True)
        for price in all_price:
            result.append(lowest_agent_price - price)

    return result

def get_level_differential_from_boutique_modelproduct(model_product):
    """从售卖商品的modelid找到虚拟商品券的差价
    """
    result = []
    find_mp = get_virtual_modelproduct_from_boutique_modelproduct(model_product.id)
    result = get_level_differential_from_coupon_modelproduct(find_mp, model_product.lowest_agent_price)

    return result

def get_level_price_from_coupon_modelproduct(find_mp, level):
    """从coupon商品的modelid找到mamalevel虚拟商品券的price
        """
    result = 0
    if find_mp:
        for product in find_mp.products:
            if level in product.name:
                return product.agent_price
    return result


def get_level_price_from_boutique_modelproduct(model_product, level):
    """从售卖商品的modelid找到虚拟商品券的level价
    """
    result = []
    find_mp = get_virtual_modelproduct_from_boutique_modelproduct(model_product.id)
    result = get_level_price_from_coupon_modelproduct(find_mp, level)

    return result

def get_onshelf_modelproducts():
    # type: () -> Optional[List[ModelProduct]]
    """获取上架商品
    """
    return ModelProduct.objects.get_onshelf_modelproducts()