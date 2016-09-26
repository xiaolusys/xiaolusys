__ALL__ = ["get_modelproduct_by_id", "get_modelproduct_by_ids", "ModelProduct", 'ModelProductCtl']

from apis.internal import get_model_by_id, get_multi_model_by_ids
from core.utils import flatten

def get_modelproduct_by_id(id):
    from flashsale.pay.models import ModelProduct
    obj = get_model_by_id({'id': id}, ModelProduct)
    return obj

def get_modelproduct_by_ids(ids):
    # ids: array of id
    from flashsale.pay.models import ModelProduct
    modelproducts = get_multi_model_by_ids({'id': ids}, ModelProduct)
    return modelproducts

class ModelProduct(object):
    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.name = kwargs['name']
        self.sku_info = kwargs['sku_info']
        self.comparison = kwargs['comparison']
        self.extras = kwargs['extras']
        self.head_imgs = kwargs['head_imgs']
        self.product_ids = kwargs['product_ids']
        self.detail_content = kwargs['detail_content']
        self.rebeta_scheme_id = kwargs['rebeta_scheme_id']

        self.is_teambuy = kwargs['is_teambuy']
        self.teambuy_price = kwargs['teambuy_price']
        self.teambuy_person_num = kwargs['teambuy_person_num']
        # TODO: Add all fields

    def get_products(self):
        if not hasattr(self, '_products_'):
            from . import product
            self._products_ = product.ProductCtl.multiple(ids=self.product_ids)
        return self._products_

    def get_skustats(self):
        if not hasattr(self, '_sku_stats_'):
            self._sku_stats_ = flatten([product.sku_items() for product in self.get_products()])
        return self._sku_stats_

    def get_rebetaschema(self):
        from flashsale.xiaolumm.models import AgencyOrderRebetaScheme
        return AgencyOrderRebetaScheme.get_rebeta_scheme(self.rebeta_scheme_id)

class ModelProductService(object):
    def retrieve(self, id):
        return get_modelproduct_by_id(id)

    def multiple(self, ids=[]):
        return get_modelproduct_by_ids(ids)

ModelProductCtl = ModelProductService()