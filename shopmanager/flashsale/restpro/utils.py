# coding: utf-8
import datetime
from django.shortcuts import get_object_or_404
from shopback.items.models import Product
from flashsale.xiaolumm.models.models_rebeta import AgencyOrderRebetaScheme
from flashsale.pay.models import Customer, CustomerShops, CuShopPros


def save_pro_info(product, user):
    """ 保存商品信息到店铺商品中 """
    customer = get_object_or_404(Customer, user=user)
    xlmm = customer.get_charged_mama()
    rebt = AgencyOrderRebetaScheme.objects.get(status=AgencyOrderRebetaScheme.NORMAL, is_default=True)
    pro = get_object_or_404(Product, id=int(product))
    shop, shop_state = CustomerShops.objects.get_or_create(customer=customer.id)
    if not shop.name:
        shop.name = customer.nick  # 保存店铺名称
        shop.save()

    shop_pro, pro_state = CuShopPros.objects.get_or_create(customer=customer.id, shop=shop.id, product=pro.id)
    kwargs = {'agencylevel': xlmm.agencylevel,
              'product_price_yuan': float(pro.agent_price)} if xlmm and pro.agent_price else {}
    rebet_amount = rebt.calculate_carry(**kwargs) if kwargs else 0  # 计算佣金

    if isinstance(pro.sale_time, datetime.date):
        offshelf_time = pro.sale_time + datetime.timedelta(days=2)
    else:
        return False, False
    if not pro.category:
        return False, False
    # 保存信息
    if pro.shelf_status == Product.DOWN_SHELF:  # 如果没有上架
        shop_pro.pro_status = CuShopPros.DOWN_SHELF  # 则保存下架状态
    shop_pro.customer = customer.id
    shop_pro.name = pro.name
    shop_pro.offshelf_time = pro.offshelf_time if pro.offshelf_time else offshelf_time
    shop_pro.pic_path = pro.pic_path
    shop_pro.std_sale_price = pro.std_sale_price
    shop_pro.agent_price = pro.agent_price
    shop_pro.remain_num = pro.remain_num
    shop_pro.carry_amount = rebet_amount
    shop_pro.carry_scheme = rebt.id
    shop_pro.pro_category = pro.category.cid
    shop_pro.model = pro.model_id  # save model info
    shop_pro.save()
    return shop_pro, pro_state

