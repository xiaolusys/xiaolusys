__ALL__ = ["get_modelproduct_by_id", "get_modelproduct_by_ids", "ModelProduct", 'ModelProductCtl']

from apis.internal import get_model_by_id, get_multi_model_by_ids
from core.utils import flatten
from flashsale.pay.models import ModelProduct as DBModelProduct


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
        self.product_type = kwargs['product_type']
        self.sku_info = kwargs['sku_info']
        self.comparison = kwargs['comparison']
        self.extras = kwargs['extras']
        self.head_imgs = kwargs['head_imgs']
        self.title_imgs = kwargs['title_imgs']
        self.product_ids = kwargs['product_ids']
        self.detail_content = kwargs['detail_content']
        self.rebeta_scheme_id = kwargs['rebeta_scheme_id']

        self.is_teambuy = kwargs['is_teambuy']
        self.teambuy_price = kwargs['teambuy_price']
        self.teambuy_person_num = kwargs['teambuy_person_num']
        self.source_type = kwargs['source_type']
        # TODO: Add all fields

    def get_products(self):
        if not hasattr(self, '_products_'):
            from . import product
            self._products_ = product.ProductCtl.multiple(ids=self.product_ids)
        return self._products_

    def get_properties(self):
        if not hasattr(self, '_properties_'):
            mp = DBModelProduct.objects.get(id=self.id)
            self._properties_ = mp.get_properties()
        return self._properties_

    def get_divide_products(self):
        """ {color: product}"""
        if not hasattr(self, '_divide_products_'):
            from shopback.items.models import Product
            from apis.v1.products.product import ProductCtl
            mp = DBModelProduct.objects.get(id=self.id)
            colors = self.get_properties()
            res = {}
            if mp.products.count() == 1:
                pid = mp.product.id
                p = ProductCtl.retrieve(pid)
                return dict([(color,p) for color in colors])
            else:
                for color in colors:
                    pro = Product.objects.filter(model_id=self.id, name__contains=color).first()
                    if not pro: continue
                    p = ProductCtl.retrieve(pro.id)
                    res[color] = p
            self._divide_products_ = res
        return self._divide_products_

    def get_divide_skus(self):
        """ {color: [skus]}"""
        if not hasattr(self, '_divide_skus_'):
            from shopback.items.models import Product
            from apis.v1.products.sku import SkuService
            mp = DBModelProduct.objects.get(id=self.id)
            colors = mp.get_properties()
            if mp.products.count() == 1:
                res = dict([(color, mp.product.get_skus_by_color(color)) for color in colors])
            else:
                res = {}
                for color in colors:
                    p = Product.objects.filter(model_id=self.id, name__contains=color).first()
                    if not p: continue
                    res[color] = p.eskus
            r2 = {}
            for color in res:
                r2[color] = []
                for sku in res[color]:
                    r2[color].append(SkuService().retrieve(sku.id))
            self._divide_skus_ = r2
        return self._divide_skus_

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