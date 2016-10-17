__ALL__ = ["get_product_by_id", "get_product_by_ids", "Product", "ProductCtl"]

from apis.internal import get_model_by_id, get_multi_model_by_ids

def get_product_by_id(id):
    from shopback.items.models import Product
    obj = get_model_by_id({'id': id}, Product)
    return obj

def get_product_by_ids(ids):
    from shopback.items.models import Product
    return get_multi_model_by_ids({'id': ids}, Product)


class Product(object):
    def __init__(self, **kwargs):
        self.sku_ids = kwargs['sku_ids']
        self.type = kwargs['type']
        self.id = kwargs['id']
        self.outer_id = kwargs['outer_id']
        self.name = kwargs['name']
        self.product_img = kwargs['product_img']
        self.agent_price = kwargs['agent_price']
        self.lowest_price = kwargs['lowest_price']
        self.std_sale_price = kwargs['std_sale_price']

    def sku_items(self):
        if not hasattr(self, '_sku_items_'):
            from . import sku
            self._sku_items_ = sku.SkuCtl.multiple(ids=self.sku_ids)
        return self._sku_items_

    def sku_stats(self):
        if not hasattr(self, '_sku_stats_'):
            from . import stat
            self._sku_stats_ = stat.SkustatCtl.multiple(ids=self.sku_ids)
        return self._sku_stats_

    def get_realtime_quantity(self):
        sku_items = self.sku_stats()
        if sku_items:
            return sum([ss.get_realtime_quantity() for ss in sku_items])
        return 0

    def get_wait_post_num(self):
        sku_items = self.sku_stats()
        if sku_items:
            return sum([ss.get_wait_post_num() for ss in sku_items])
        return 0

    def get_lock_num(self):
        sku_items = self.sku_stats()
        if sku_items:
            return sum([ss.get_lock_num() for ss in sku_items])
        return 0


class ProductService(object):
    def retrieve(self, id):
        return get_product_by_id(id)

    def multiple(self, ids=[]):
        return get_product_by_ids(ids)

ProductCtl = ProductService()