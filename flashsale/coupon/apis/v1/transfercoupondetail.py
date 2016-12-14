# coding=utf-8
from __future__ import unicode_literals, absolute_import
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


def create_transfer_coupon_detail(transfer_id, transfer_type, coupon_ids):
    # type: (int, int, List[int]) -> List[TransferCouponDetail]
    """创建 流通记录 明细 内容
    """
    from ...models.transfercoupondetail import TransferCouponDetail

    coupon_ids = set(coupon_ids)
    ds = []
    with transaction.atomic():
        for coupon_id in coupon_ids:
            d, state = TransferCouponDetail.objects.get_or_create(
                transfer_id=transfer_id,
                coupon_id=coupon_id
            )
            d.transfer_type = transfer_type
            d.save()
            ds.append(d)
    return ds
