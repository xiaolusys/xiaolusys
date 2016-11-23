# coding=utf-8
from __future__ import unicode_literals, absolute_import
from core.managers import BaseManager
import logging

logger = logging.getLogger(__name__)


class ModelProductManager(BaseManager):
    def get_query_set(self):
        _super = super(BaseManager, self)
        if hasattr(_super, 'get_query_set'):
            return _super.get_query_set()
        return _super.get_queryset()
    get_queryset = get_query_set

    def get_virtual_modelproducts(self):
        # type: () -> Optional[List[ModelProduct]]
        """获取虚拟商品记录
        """
        return self.get_queryset().filter(product_type=self.model.VIRTUAL_TYPE, status=self.model.NORMAL)