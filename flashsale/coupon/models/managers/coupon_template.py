# coding=utf-8
from __future__ import absolute_import, unicode_literals
import logging
from core.managers import BaseManager

logger = logging.getLogger(__name__)


class UserCouponTemplateManager(BaseManager):
    def get_query_set(self):
        _super = super(BaseManager, self)
        if hasattr(_super, 'get_query_set'):
            return _super.get_query_set()
        return _super.get_queryset()

    get_queryset = get_query_set

    def get_refund_templates(self):
        # type: () -> Optional[List[SaleRefund]]
        """　获取退款补偿类型优惠券模板
        """
        return self.get_queryset().filter(coupon_type=self.model.TYPE_COMPENSATE, status=self.model.SENDING)

    def get_boutique_templates(self):
        return self.get_queryset().filter(coupon_type=self.model.TYPE_TRANSFER)

    def get_template_to_modelproduct_maps(self):
        boutique_qs = self.get_boutique_templates()
        tmp_values = boutique_qs.values_list('id', 'extras')
        return dict([(k, s['scopes'].get('modelproduct_ids')) for k, s in tmp_values])