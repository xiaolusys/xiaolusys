# coding=utf-8
from core.models import BaseModel
from django.db import models
from django.db.models.signals import post_save


class TmpShareCoupon(BaseModel):
    mobile = models.CharField(max_length=11, db_index=True, verbose_name=u'手机号')  # type: text_type
    share_coupon_id = models.CharField(db_index=True, max_length=32, verbose_name=u"分享uniq_id")  # type: text_type
    status = models.BooleanField(default=False, db_index=True, verbose_name=u'是否领取')  # type: bool
    value = models.FloatField(default=0.0, verbose_name=u'优惠券价值')  # type: float

    class Meta:
        unique_together = ('mobile', 'share_coupon_id')  # 一个分享 一个手机号只能领取一次
        db_table = "flashsale_user_tmp_coupon"
        app_label = 'coupon'
        verbose_name = u"特卖/优惠券/用户临时优惠券表"
        verbose_name_plural = u"特卖/优惠券/用户临时优惠券列表"

    def __unicode__(self):
        # type: () -> text_type
        return "<%s,%s>" % (self.id, self.mobile)


def update_mobile_download_record(sender, instance, created, **kwargs):
    # type: (Any, TmpShareCoupon, bool, **Any) -> None
    from flashsale.coupon.tasks.usercoupon import task_update_mobile_download_record

    task_update_mobile_download_record.delay(instance)


post_save.connect(update_mobile_download_record, sender=TmpShareCoupon,
                  dispatch_uid='post_save_update_mobile_download_record')

