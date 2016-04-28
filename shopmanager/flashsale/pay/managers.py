# -*- coding:utf8 -*-
import datetime
import random

from core.managers import BaseManager


class NormalSaleTradeManager(BaseManager):
    def get_queryset(self):
        _super = super(NormalSaleTradeManager, self)
        queryset = _super.get_queryset()
        return queryset.filter(
            status__in=self.model.NORMAL_TRADE_STATUS
        ).order_by('-created')


class NormalUserAddressManager(BaseManager):
    def get_queryset(self):
        queryset = super(NormalUserAddressManager, self).get_queryset()
        return queryset.filter(status=self.model.NORMAL).order_by('-created')


from . import constants


class ShopProductCategoryManager(BaseManager):
    def child_query(self):
        """ 童装产品 """
        pro_category = constants.CHILD_CID_LIST
        return self.get_queryset().filter(pro_category__in=pro_category).order_by("-position")

    def female_query(self):
        """ 女装产品 """
        pro_category = constants.FEMALE_CID_LIST
        return self.get_queryset().filter(pro_category__in=pro_category).order_by("-position")


class UserCouponManager(BaseManager):
    def create_by_template(self, buyer_id, template_id, trade_id=None, batch_no=None, ufrom=None, **kwargs):
        """
        发放不绑定交易的任何类型的优惠券
        """
        from flashsale.pay.models_share_coupon import UserCoupon, CouponTemplate

        trade_id = trade_id or ''
        if not (buyer_id and template_id):
            return None, 7, u'没有发放'
        try:
            tpl = CouponTemplate.objects.get(id=int(template_id), valid=True)  # 获取优惠券模板
            now = datetime.datetime.now()
            if not (tpl.release_start_time <= now <= tpl.release_end_time):
                return None, 6, u"没有发放"  # 不在模板定义的发放时间内
        except CouponTemplate.DoesNotExist:
            return None, 5, u"没有发放"
        # 身份判定（判断身份是否和优惠券模板指定用户一致） 注意　这里是硬编码　和　XiaoluMama　代理级别关联
        user_level = CouponTemplate.ALL_USER
        from flashsale.pay.models import Customer

        customer = Customer.objects.get(id=int(buyer_id))
        if tpl.target_user != CouponTemplate.ALL_USER:  # 如果不是所有用户可领取则判定级别
            xlmm = customer.getXiaolumm()
            if xlmm:
                user_level = xlmm.agencylevel  # 用户的是代理身份 内1 　VIP 2  A 3

        if user_level != tpl.target_user:
            # 如果用户领取的优惠券和用户身份不一致则不予领取
            return None, 4, u"用户不一致"
        coupons = UserCoupon.objects.filter(template_id=template_id)

        tpl_release_count = coupons.count()
        if tpl_release_count > tpl.nums:  # 如果大于定义的限制领取数量
            return None, 3, u"优惠券已经发完了"
        user_coupon_count = coupons.filter(customer=int(buyer_id)).count()
        batch_no = batch_no or ''
        if tpl.type != CouponTemplate.SHARE:  # 分享类型没有领取限制(即不是分享类型的需要校验领取限制张数)
            if user_coupon_count >= tpl.limit_num:
                return None, 2, u"领取超过限制"
        else:  # 如果是分享类型
            if not batch_no:  # 如果分享类型没有分享批次号码则不予领取优惠券
                return None, 1, u"没有领取到呢"
        value = tpl.value
        start_use_time = tpl.start_use_time
        deadline = tpl.deadline

        if tpl.type == CouponTemplate.SHARE:
            if tpl.is_random and tpl.max_value and tpl.min_value:  # 分享类型 并且设置随机
                value = float('%.1f' % random.uniform(tpl.max_value, tpl.min_value))  # 生成随机的value
            if tpl.valid_days:
                start_use_time = 1  # 今天
                deadline = 1  # 今天+tpl.valid_days
        ufrom = ufrom or ''
        template_num_unique = str(tpl.id) + "_" + str(user_coupon_count + 1)  # 唯一键约束 是 优惠id + "_" + 该优惠券领取张数
        cou = UserCoupon.objects.create(template_id=int(template_id),
                                        title=tpl.title,
                                        type=tpl.type,
                                        way_type=tpl.way_type,
                                        customer=int(buyer_id),
                                        batch_no=batch_no,
                                        nick=customer.nick,
                                        thumbnail=customer.thumbnail,
                                        value=value,
                                        sale_trade=str(trade_id),
                                        start_use_time=start_use_time,
                                        deadline=deadline,
                                        ufrom=ufrom,
                                        template_num_unique=template_num_unique)
        return cou, 0, u"领取成功"
