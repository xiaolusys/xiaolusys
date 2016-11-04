# coding=utf-8
from core.models import BaseModel
from django.db import models
from core.fields import JSONCharMyField
from django.db.models.signals import pre_save
from ..managers import OrderShareCouponManager


def default_share_extras():
    # type: () -> Dict[str, Any]
    return {
        'user_info': {'id': None, 'nick': '', 'thumbnail': ''},
        "templates": {"post_img": '', "description": '', "title": ''}
    }


class OrderShareCoupon(BaseModel):
    WX = u'wx'
    PYQ = u'pyq'
    QQ = u'qq'
    QQ_SPA = u'qq_spa'
    SINA = u'sina'
    WAP = u'wap'
    PLATFORM = ((WX, u"微信好友"), (PYQ, u"朋友圈"), (QQ, u"QQ好友"),
                (QQ_SPA, u"QQ空间"), (SINA, u"新浪微博"), (WAP, u'wap'))
    SENDING = 0
    FINISHED = 1
    STATUS_CHOICES = (
        (SENDING, u'发放中'),
        (FINISHED, u'已结束'))
    template_id = models.IntegerField(db_index=True, verbose_name=u"模板ID")  # type: int
    share_customer = models.IntegerField(db_index=True, verbose_name=u'分享用户')  # type: int
    uniq_id = models.CharField(max_length=32, unique=True, verbose_name=u"唯一ID")  # type: text_type  # 交易的tid

    release_count = models.IntegerField(default=0, verbose_name=u"领取次数")  # type: int  # 该分享下 优惠券被领取成功次数
    has_used_count = models.IntegerField(default=0, verbose_name=u"使用次数")  # type: int  # 该分享下产生优惠券被使用的次数
    limit_share_count = models.IntegerField(default=0, verbose_name=u"最大领取次数")  # type: int

    platform_info = JSONCharMyField(max_length=128, blank=True, default='{}',
                                    verbose_name=u"分享到平台记录")  # type: text_type
    share_start_time = models.DateTimeField(blank=True, verbose_name=u"分享开始时间")  # type: Optional[datetime.datetime]
    share_end_time = models.DateTimeField(blank=True, db_index=True,
                                          verbose_name=u"分享截止时间")  # type: Optional[datetime.datetime]

    # 用户点击分享的时候 判断如果达到最大分享次数了 修改该状态到分享结束
    status = models.IntegerField(default=SENDING, db_index=True, choices=STATUS_CHOICES,
                                 verbose_name=u"状态")  # type: int
    extras = JSONCharMyField(max_length=1024, default=default_share_extras, blank=True, null=True,
                             verbose_name=u"附加信息")  # type: Optional[text_type]
    objects = OrderShareCouponManager()

    class Meta:
        db_table = "flashsale_coupon_share_batch"
        app_label = 'coupon'
        verbose_name = u"特卖/优惠券/订单分享表"
        verbose_name_plural = u"特卖/优惠券/订单分享列表"

    def __unicode__(self):
        # type: () -> text_type
        return "<%s,%s>" % (self.id, self.template_id)

    @property
    def nick(self):
        # type: () -> text_type
        """分享者昵称"""
        return self.extras['user_info']['nick']

    @property
    def thumbnail(self):
        # type: () -> text_type
        """分享者的头像"""
        return self.extras['user_info']['thumbnail']

    @property
    def post_img(self):
        # type: () -> text_type
        """模板的图片链接"""
        return self.extras['templates']['post_img']

    @property
    def description(self):
        # type: () -> text_type
        """模板的描述"""
        return self.extras['templates']['description']

    @property
    def title(self):
        # type: () -> text_type
        """模板的标题"""
        return self.extras['templates']['title']

    @property
    def template(self):
        # type: () -> Optional[CouponTemplate]
        from .coupon_template import CouponTemplate
        return CouponTemplate.objects.filter(id=self.template_id).first()

    @property
    def remain_num(self):
        # type: () -> int
        """ 还剩下多少次没领取 """
        return self.limit_share_count - self.release_count


def coupon_share_xlmm_newtask(sender, instance, **kwargs):
    # type: (Any, Any, **Any) -> None
    """
    检测新手任务：分享第一个红包
    """
    from flashsale.xiaolumm.tasks_mama_push import task_push_new_mama_task
    from flashsale.xiaolumm.models.new_mama_task import NewMamaTask
    from flashsale.pay.models.user import Customer

    coupon_share = instance
    customer_id = coupon_share.share_customer
    customer = Customer.objects.filter(id=customer_id).first()
    if not customer:
        return

    xlmm = customer.getXiaolumm()
    coupon_share = OrderShareCoupon.objects.filter(share_customer=customer_id).exists()

    if xlmm and not coupon_share:
        task_push_new_mama_task.delay(xlmm, NewMamaTask.TASK_FIRST_SHARE_COUPON)


pre_save.connect(coupon_share_xlmm_newtask,
                 sender=OrderShareCoupon, dispatch_uid='pre_save_coupon_share_xlmm_newtask')

