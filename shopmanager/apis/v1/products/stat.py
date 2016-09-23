__ALL__ = ["get_sku_stat_by_id", "get_sku_stat_by_ids", "Skustat", "SkustatCtl"]

from apis.internal import get_model_by_id, get_multi_model_by_ids

def get_product_stat_by_id(id):
    pass

def get_product_stat_by_ids(ids):
    pass

def get_sku_stat_by_id(id):
    from shopback.items.models import ProductSkuStats
    obj = get_model_by_id({'sku_id': id}, ProductSkuStats)
    return obj

def get_sku_stat_by_ids(ids):
    from shopback.items.models import ProductSkuStats
    return get_multi_model_by_ids({'sku_id': ids}, ProductSkuStats)


class Skustat(object):
    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.sku_id = kwargs['id']
        self.assign_num = kwargs['assign_num']
        self.inferior_num = kwargs['inferior_num']
        self.adjust_quantity = kwargs['adjust_quantity']
        self.history_quantity = kwargs['history_quantity']
        self.inbound_quantity = kwargs['inbound_quantity']
        self.return_quantity = kwargs['return_quantity']
        self.rg_quantity = kwargs['rg_quantity']
        self.post_num = kwargs['post_num']
        self.sold_num = kwargs['sold_num']
        self.shoppingcart_num = kwargs['shoppingcart_num']
        self.waitingpay_num = kwargs['waitingpay_num']
        self.remain_num = kwargs['remain_num']

    def get_lock_num(self):
        return self.shoppingcart_num + self.waitingpay_num + self.sold_num - self.return_quantity - self.post_num

    def get_free_num(self):
        return max(self.remain_num - max(self.get_lock_num(), 0), 0)

    def is_saleout(self):
        return self.get_free_num() <= 0

class SkustatService(object):
    def retrieve(self, id):
        return get_sku_stat_by_id(id)

    def multiple(self, ids=[]):
        return get_sku_stat_by_ids(ids)

SkustatCtl = SkustatService()



