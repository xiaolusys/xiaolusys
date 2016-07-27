# coding: utf-8
from django.core.cache import cache

from common import cacheable
from flashsale.xiaolumm.models.models_rebeta import AgencyOrderRebetaScheme
from shopback.categorys.models import ProductCategory


class RebetaSchemaCache(cacheable.LocalCacheable):
    cache_time = 30 * 60
    cache_key  = '%s.%s'%(__name__, 'RebetaSchemaCache')
    def __init__(self):
        super(RebetaSchemaCache, self).__init__()

    # def load(self):
    #     # data = []
    #     # # TODO 要考虑数据变更及model更新产生异常
    #     # for row in AgencyOrderRebetaScheme.objects.filter(
    #     #         status=AgencyOrderRebetaScheme.NORMAL):
    #     #     data.append({'id': row.id, 'name': row.name})
    #     # self.data = data

    @property
    # @cacheable.LocalCacheable.reload
    def schemas(self):
        cache_value = cache.get(self.cache_key)
        if not cache_value:
            cache_value = []
            # TODO@meron cache失效应过期
            for row in AgencyOrderRebetaScheme.objects.filter(
                    status=AgencyOrderRebetaScheme.NORMAL):
                cache_value.append({'id': row.id, 'name': row.name})
            cache.set(self.cache_key, cache_value, self.cache_time)
        return cache_value


class ProductCategoryCache(cacheable.LocalCacheable):
    EX_NAMES = ['小鹿美美', '优尼世界']
    cache_time = 30 * 60
    cache_key = '%s.%s' % (__name__, 'ProductCategoryCache')
    def __init__(self):
        super(ProductCategoryCache, self).__init__()

    # def load(self):
    #     data = []
    #     # TODO 要考虑数据变更及model更新产生异常
    #     for row in ProductCategory.objects.filter(is_parent=True).exclude(
    #             name__in=self.EX_NAMES).order_by('cid'):
    #         data.append({'id': row.cid, 'name': unicode(row)})
    #     self.data = data

    @property
    # @cacheable.LocalCacheable.reload
    def categories(self):
        cache_value = cache.get(self.cache_key)
        if not cache_value:
            cache_value = []
            # TODO@meron cache失效应过期
            for row in ProductCategory.objects.filter(is_parent=True).exclude(
                    name__in=self.EX_NAMES).order_by('cid'):
                cache_value.append({'id': row.cid, 'name': unicode(row)})
            cache.set(self.cache_key, cache_value, self.cache_time)
        return cache_value


rebeta_schema_cache = RebetaSchemaCache()
product_category_cache = ProductCategoryCache()