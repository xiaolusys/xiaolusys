# coding=utf-8
from __future__ import absolute_import, unicode_literals
import logging
from core.managers import BaseManager

logger = logging.getLogger(__name__)


class UserCouponManager(BaseManager):
    def get_query_set(self):
        _super = super(BaseManager, self)
        if hasattr(_super, 'get_query_set'):
            return _super.get_query_set()
        return _super.get_queryset()

    get_queryset = get_query_set

    def get_template_coupons(self, coupon_template_id):
        # type: (int) -> Optional[List[UserCoupon]]
        """指定模板的优惠券
        """
        return self.get_queryset().filter(template_id=coupon_template_id).exclude(status=self.model.CANCEL)

    def get_unused_coupons(self):
        # type: () -> Optional[List[UserCoupon]]
        """获取没有使用的用户优惠券
        """
        return self.get_queryset().filter(status=self.model.UNUSED)
