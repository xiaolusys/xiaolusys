# coding=utf-8
from __future__ import unicode_literals, absolute_import
from core.managers import BaseManager
from .. import constants
import logging

logger = logging.getLogger(__name__)


class ShopProductCategoryManager(BaseManager):
    def child_query(self):
        # type: () -> Optional[List[CuShopPros]]
        """童装产品
        """
        pro_category = constants.CHILD_CID_LIST
        return self.get_queryset().filter(pro_category__in=pro_category).order_by("-position")

    def female_query(self):
        # type: () -> Optional[List[CuShopPros]]
        """女装产品
        """
        pro_category = constants.FEMALE_CID_LIST
        return self.get_queryset().filter(pro_category__in=pro_category).order_by("-position")
