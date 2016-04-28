# coding= utf-8
"""
模板：负责优惠券的定义（用途，价值，标题）
分享批次：负责分享时候生成批次记录,绑定交易,用户,使用模板
用户：负责记录用户优惠券持有状态,使用价值等信息
"""
import datetime
from django.db import models
from options import uniqid
from core.models import BaseModel
from core.fields import JSONCharMyField


class CouponTemplate(BaseModel):
    USUAL = 1
    SHARE = 2
    PROMOTION = 3

    COUPON_TYPE = ((USUAL, u"普通"), (SHARE, u"分享类型"), (PROMOTION, u"活动类型"))

    CLICK_WAY = 1
    BUY_WAY = 2
    XMM_LINK = 3
    PROMOTION_WAY = 4
    COUPON_WAY = ((CLICK_WAY, u"点击方式领取"), (BUY_WAY, u"购买商品获取"),
                  (XMM_LINK, u"购买专属链接"), (PROMOTION_WAY, u"活动发放"))
    ALL_USER = 1
    AGENCY_VIP = 2
    AGENCY_A = 3
    TAR_USER = ((ALL_USER, u"所有用户"), (AGENCY_A, u"A类代理"), (AGENCY_VIP, u"VIP代理"))

    title = models.CharField(max_length=64, verbose_name=u"优惠券标题")
    value = models.FloatField(default=1.0, verbose_name=u"优惠券价值")

    max_value = models.FloatField(default=0.0, verbose_name=u'优惠券最大值')  # 用于生成随机的分享优惠时候使用
    min_value = models.FloatField(default=0.0, verbose_name=u'优惠券最小值')
    is_random = models.BooleanField(default=False, db_index=True, verbose_name=u"是否随机金额")

    valid = models.BooleanField(default=False, verbose_name=u"是否有效")
    type = models.IntegerField(choices=COUPON_TYPE, verbose_name=u"优惠券类型")
    nums = models.IntegerField(default=0, verbose_name=u"发放数量")
    limit_num = models.IntegerField(default=1, verbose_name=u"每人领取数量")

    use_fee = models.FloatField(default=0.0, verbose_name=u'满多少元可以使用')  # 满多少可以使用
    release_fee = models.FloatField(default=0.0, verbose_name=u'满多少元可以发放')  # 满多少可以发放

    bind_pros = models.CharField(max_length=256, null=True, blank=True, verbose_name=u'绑定可以使用的产品')  # 指定产品可用

    use_pro_category = models.CharField(max_length=256, blank=True, verbose_name=u'可以使用产品的类别')

    release_start_time = models.DateTimeField(blank=True, verbose_name=u'开始发放的时间')
    release_end_time = models.DateTimeField(blank=True, verbose_name=u'结束发放的时间')

    start_use_time = models.DateTimeField(blank=True, verbose_name=u'开始使用的时间')

    deadline = models.DateTimeField(blank=True, verbose_name=u'截止使用的时间')

    valid_days = models.IntegerField(default=0, verbose_name=u'分享领取有效时间')  # 用户点击分享类型领取优惠券有效天数
    share_times_limit = models.IntegerField(default=5, verbose_name=u'定义分享被领取次数')  # 分享链接被成功领取的优惠券次数

    use_notice = models.TextField(blank=True, verbose_name=u"使用须知")
    way_type = models.IntegerField(default=0, choices=COUPON_WAY, verbose_name=u"领取途径")
    target_user = models.IntegerField(default=0, choices=TAR_USER, verbose_name=u"目标用户")
    post_img = models.CharField(max_length=512, blank=True, null=True, verbose_name=u"模板图片")

    class Meta:
        db_table = "pay_share_coupon_template"
        app_label = 'pay'
        verbose_name = u"特卖/分享/优惠券/模板"
        verbose_name_plural = u"特卖/分享/优惠券/模板列表"

    def __unicode__(self):
        return '<%s,%s>' % (self.id, self.title)

    def template_valid_check(self):
        """
        模板检查
        """
        if not self.valid:
            raise AssertionError(u"无效优惠券")
        else:
            return self

    def usefee_check(self, fee):
        """
        满单额条件检查　
        :param fee 交易金额
        """
        if self.use_fee == 0:
            return
        elif self.use_fee > fee:
            raise AssertionError(u'该优惠券满%s元可用' % self.use_fee)

    def check_date(self):
        """ 检查有效天数（匹配截止日期）"""
        # 判断当前时间是否在　有效时间内
        now = datetime.datetime.now()
        if self.start_use_time <= now <= self.deadline:
            return
        else:
            raise AssertionError(u'%s至%s可以使用' % (self.start_use_time, self.deadline))

    def check_category(self, product_ids=None):
        """ 可用分类检查 """
        if not self.use_pro_category:  # 没有设置分类限制信息　则为全部分类可以使用
            return
        from shopback.items.models import Product

        tpl_categorys = self.use_pro_category.strip().split(',') if self.use_pro_category else []
        pros_categorys = Product.objects.filter(id__in=product_ids).values('category_id')
        category_ids = [str(i['category_id']) for i in pros_categorys]

        set_tpl_categorys = set(tpl_categorys)
        set_category = set(category_ids)
        if len(set_tpl_categorys & set_category) == 0:  # 比较分类 如果没有存在的分类则报错
            raise AssertionError(u'该产品不支持使用优惠券')
        return

    def check_bind_pros(self, product_ids=None):
        """ 检查绑定的产品 """
        tpl_bind_pros = self.bind_pros.strip().split(',') if self.bind_pros else []
        if not tpl_bind_pros != []:  # 如果优惠券没有绑定产品
            self.check_category(product_ids)  # 没有限制产品则检查分类限制
            return
        product_str_ids = [str(i) for i in product_ids]
        tpl_binds = set(tpl_bind_pros)
        pro_set = set(product_str_ids)
        if len(tpl_binds & pro_set) == 0:
            raise AssertionError(u'该产品不支持使用优惠券')
        # 检查产品后检查分类
        self.check_category(product_ids)

    def use_fee_desc(self):
        """ 满单额描述 """
        return "满{0}可用".format(self.use_fee)

    def pros_desc(self):
        """ 绑定产品描述 """
        if self.bind_pros:
            return '指定产品可用'
        else:
            return '全场通用'


def default_batch_no():
    return uniqid('%s%s' % ('bc', datetime.datetime.now().strftime('%y%m%d')))


class CouponShareBatch(BaseModel):
    WX = u'wx'
    PYQ = u'pyq'
    QQ = u'qq'
    QQ_SPA = u'qq_spa'
    SINA = u'sina'
    WAP = u'wap'
    PLATFORM = ((WX, u"微信好友"), (PYQ, u"朋友圈"), (QQ, u"QQ好友"), (QQ_SPA, u"QQ空间"), (SINA, u"新浪微博"), (WAP, u'wap'))

    template_choose = models.IntegerField(db_index=True, verbose_name=u"模板ID")
    share_customer = models.IntegerField(db_index=True, verbose_name=u'分享用户')
    nick = models.CharField(max_length=32, blank=True, verbose_name=u'分享用户的昵称')
    thumbnail = models.CharField(max_length=256, blank=True, verbose_name=u'分享用户的头像')

    batch_no = models.CharField(max_length=32, unique=True,
                                default=default_batch_no, verbose_name=u"分享批次号码")
    bind_trade = models.CharField(max_length=32, unique=True, verbose_name=u"绑定交易")

    touch_times = models.IntegerField(default=0, verbose_name=u"分享被访问次数")
    share_times_limit = models.IntegerField(default=0, verbose_name=u"分享红包领取限制次数")

    platform_info = JSONCharMyField(max_length=128, blank=True, default='{}', verbose_name=u"分享到平台记录")
    share_start_time = models.DateTimeField(blank=True, verbose_name=u"分享开始时间")
    deadline = models.DateTimeField(blank=True, verbose_name=u"分享截止时间")

    class Meta:
        db_table = "pay_share_coupon_batch"
        app_label = 'pay'
        verbose_name = u"特卖/优惠券/分享批次表"
        verbose_name_plural = u"优惠券/券池/分享批次列表"

    def __unicode__(self):
        return "<%s,%s>" % (self.id, self.template_choose)


def default_coupon_no():
    return uniqid('%s%s' % ('YH', datetime.datetime.now().strftime('%y%m%d')))


from flashsale.pay.managers import UserCouponManager


class UserCoupon(BaseModel):
    USUAL = 1
    SHARE = 2
    PROMOTION = 3
    COUPON_TYPE = ((USUAL, u"普通"), (SHARE, u"分享类型"), (PROMOTION, u"活动类型"))

    USED = 1
    UNUSED = 0
    FREEZE = 2
    PAST = 3
    USER_COUPON_STATUS = ((UNUSED, u"未使用"), (USED, u"已使用"), (FREEZE, u"冻结中"), (PAST, u"已经过期"))

    CLICK_WAY = 1
    BUY_WAY = 2
    XMM_LINK = 3
    PROMOTION_WAY = 4
    COUPON_WAY = ((CLICK_WAY, u"点击方式领取"), (BUY_WAY, u"购买商品获取"),
                  (XMM_LINK, u"购买专属链接"), (PROMOTION_WAY, u"活动发放"))

    WX = u'wx'
    PYQ = u'pyq'
    QQ = u'qq'
    QQ_SPA = u'qq_spa'
    SINA = u'sina'
    WAP = u'wap'
    PLATFORM = ((WX, u"微信好友"), (PYQ, u"朋友圈"), (QQ, u"QQ好友"),
                (QQ_SPA, u"QQ空间"), (SINA, u"新浪微博"), (WAP, u'wap'))

    template_id = models.IntegerField(db_index=True, verbose_name=u"优惠券id")
    title = models.CharField(max_length=64, verbose_name=u"优惠券标题")
    type = models.IntegerField(choices=COUPON_TYPE, db_index=True, verbose_name=u"优惠券类型")
    way_type = models.IntegerField(default=0, choices=COUPON_WAY, db_index=True, verbose_name=u"领取途径")

    customer = models.IntegerField(db_index=True, verbose_name=u"顾客ID")

    batch_no = models.CharField(db_index=True, blank=True, verbose_name=u"分享批次号码")
    coupon_no = models.CharField(max_length=32, unique=True,
                                 default=default_coupon_no, verbose_name=u"优惠券号码")

    nick = models.CharField(max_length=32, blank=True, verbose_name=u'用户昵称')
    thumbnail = models.CharField(max_length=256, blank=True, verbose_name=u'用户头像')
    value = models.FloatField(verbose_name=u"优惠券价值")
    sale_trade = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u"绑定交易ID")
    start_use_time = models.DateTimeField(db_index=True, verbose_name=u"开始使用时间")
    deadline = models.DateTimeField(db_index=True, verbose_name=u"截止时间")
    ufrom = models.CharField(max_length=8, choices=PLATFORM, db_index=True, blank=True, verbose_name=u'领取平台')
    template_num_unique = models.CharField(unique=True, verbose_name=u"模板领取唯一标识")
    status = models.IntegerField(default=UNUSED, choices=USER_COUPON_STATUS, verbose_name=u"使用状态")

    objects = UserCouponManager()

    class Meta:
        db_table = "pay_share_user_coupon"
        app_label = 'pay'
        verbose_name = u"特卖/优惠券/用户优惠券表"
        verbose_name_plural = u"优惠券/用户优惠券列表"

    def __unicode__(self):
        return "<%s,%s>" % (self.id, self.customer)

    def coupon_basic_check(self):
        """
        日期检测 & 状态检查
        """
        now = datetime.datetime.now()
        coupon = self.__class__.objects.get(id=self.id)
        if coupon.status == UserCoupon.USED:
            raise AssertionError(u"优惠券已使用")
        elif coupon.status == UserCoupon.FREEZE:
            raise AssertionError(u"优惠券已冻结")
        elif coupon.status == UserCoupon.PAST:
            raise AssertionError(u"优惠券已过期")
        if not (coupon.start_use_time <= now <= coupon.deadline):
            raise AssertionError(u"使用日期错误")
        return coupon

    def check_user_coupon(self, product_ids=None, use_fee=None):
        """  用户优惠券检查是否可用 """
        tpl = CouponTemplate.objects.get(id=self.template_id)
        tpl.check_bind_pros(product_ids=product_ids)  # 绑定产品检查
        tpl.template_valid_check()  # 模板有效性检查
        tpl.usefee_check(use_fee)  # 优惠券状态检查
        self.coupon_basic_check()  # 基础检查
        return

    def use_coupon(self):
        """ 使用优惠券 """
        self.coupon_basic_check()  # 基础检查
        self.status = self.USED
        self.save()

    def freeze_coupon(self):
        """ 冻结优惠券 """
        coupon = self.__class__.objects.get(id=self.id)
        if coupon.status != UserCoupon.UNUSED:
            raise AssertionError(u"优惠券不在未使用状态,冻结失败")
        self.status = self.FREEZE
        self.save()

    def unfreeze_coupon(self):
        """ 解冻优惠券 """
        coupon = self.__class__.objects.get(id=self.id)
        if coupon.status != UserCoupon.FREEZE:
            raise AssertionError(u"优惠券不在冻结状态,解冻出错")
        self.status = self.UNUSED
        self.save()
