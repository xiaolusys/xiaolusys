# coding: utf-8

from common import cacheable
from flashsale.xiaolumm.models_rebeta import AgencyOrderRebetaScheme
from shopback.categorys.models import ProductCategory


class RebetaSchemaCache(cacheable.LocalCacheable):

    def __init__(self):
        super(RebetaSchemaCache, self).__init__()

    def load(self):
        data = []
        for row in AgencyOrderRebetaScheme.objects.filter(
                status=AgencyOrderRebetaScheme.NORMAL):
            data.append({'id': row.id, 'name': row.name})
        self.data = data

    @property
    @cacheable.LocalCacheable.reload
    def schemas(self):
        return self.data


class ProductCategoryCache(cacheable.LocalCacheable):
    EX_NAMES = ['小鹿美美', '优尼世界']

    def __init__(self):
        super(ProductCategoryCache, self).__init__()

    def load(self):
        data = []
        for row in ProductCategory.objects.filter(is_parent=True).exclude(
                name__in=self.EX_NAMES).order_by('cid'):
            data.append({'id': row.cid, 'name': unicode(row)})
        self.data = data

    @property
    @cacheable.LocalCacheable.reload
    def categories(self):
        return self.data


rebeta_schema_cache = RebetaSchemaCache()
product_category_cache = ProductCategoryCache()
