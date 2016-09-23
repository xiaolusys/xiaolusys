__ALL__ = ["get_sku_by_id", "get_sku_by_ids", "SKU", "SkuCtl"]

from apis.internal import get_model_by_id, get_multi_model_by_ids

def get_sku_by_id(id):
    from shopback.items.models import ProductSku
    obj = get_model_by_id({'id': id}, ProductSku)
    return obj

def get_sku_by_ids(ids):
    from shopback.items.models import ProductSku
    return get_multi_model_by_ids({'id': ids}, ProductSku)


class SKU(object):
    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.type = kwargs['type']
        self.name = kwargs['name']
        self.std_sale_price = kwargs['std_sale_price']
        self.agent_price = kwargs['agent_price']
        self.remain_num  = kwargs['remain_num']

class SkuService(object):
    def retrieve(self, id):
        return get_sku_by_id(id)

    def multiple(self, ids=[]):
        return get_sku_by_ids(ids)

SkuCtl = SkuService()