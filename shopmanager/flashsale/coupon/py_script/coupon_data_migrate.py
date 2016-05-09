# coding=utf-8
__author__ = 'jie.lin'

"""
历史优惠券数据迁移
step1. 模板数据迁移
       1.1 保持模板的id绝对不变
       1.2 保持模板价值数据绝对不变
       1.3 保持有效时间绝对不变
       1.4 模板类型数据迁移后手动修改(迁移时默认普通类型)
       1.5 不删除id
       1.6 如果存在id则修改内容与历史数据保持1.1-1.5内容一致
       1.7 全量迁移

step2. 手动后台修改优惠券模板的类型 以及其他字段信息(为step3做准备)

step3. 用户优惠券数据迁移
       3.1 全量迁移
       3.2 保持优惠券的价值绝对不变
       3.3 保持优惠券的使用状态绝对不变
       3.4 保持优惠券的绑定交易绝对不变
       3.5 保持优惠券的优惠券类型绝对不变
       3.6 保持优惠券的模板id绝对不变
       3.7 保持优惠券的用户信息绝对不变
       3.8 唯一标识使用优惠券模板id+优惠券模板类型+用户id
       3.9 以前一个模板可以领取多张的由程序异常抛出不做处理(废弃选用普通模板的多张领取优惠券)
       3.10 退款补偿的优惠券发放的时候要填写退款单的id
"""
from flashsale.pay.models import CouponTemplate as OTP
from flashsale.pay.models import UserCoupon as OUC
from flashsale.pay.models import CouponsPool as CPL

from flashsale.coupon.models import CouponTemplate, OrderShareCoupon, UserCoupon
import logging

logger = logging.getLogger(__name__)


def migrate_template_data():
    """ 模板数据迁移 """
    old_tpls = OTP.objects.all()

    for old_tpl in old_tpls:
        template = CouponTemplate.objects.filter(id=old_tpl.id).first()
        if template:  # 存在即修改
            template.title = old_tpl.title
            template.description = old_tpl.use_notice
            template.value = old_tpl.value
            template.prepare_release_num = old_tpl.nums
            template.release_start_time = old_tpl.release_start_time
            template.release_end_time = old_tpl.release_end_time
            template.use_deadline = old_tpl.deadline
            template.has_released_count = CPL.objects.filter(template_id=old_tpl.id).count()
            template.has_used_count = OUC.objects.filter(cp_id__template_id=old_tpl.id, status=OUC.USED).count()
            template.scope_type = CouponTemplate.SCOPE_OVERALL
            if old_tpl.bind_pros and old_tpl.bind_pros.strip():
                template.scope_type = CouponTemplate.SCOPE_PRODUCT
            if old_tpl.use_pro_category and old_tpl.use_pro_category.strip():
                template.scope_type = CouponTemplate.SCOPE_CATEGORY
            if old_tpl.valid:  # 历史有效则设置 为发放中
                template.status = CouponTemplate.SENDING
            else:
                template.status = CouponTemplate.CANCEL
            template.extras = {
                'release': {
                    'use_min_payment': old_tpl.use_fee,  # 满多少可以使用
                    'release_min_payment': old_tpl.release_fee,  # 满多少可以发放
                    'use_after_release_days': 0,  # 发放多少天后可用
                    'limit_after_release_days': 0,  # 发放多少天内可用
                    'share_times_limit': 20  # 分享链接被成功领取的优惠券次数
                },
                'randoms': {'min_val': 0, 'max_val': 1},  # 随机金额范围
                'scopes': {'product_ids': old_tpl.bind_pros, 'category_ids': old_tpl.use_pro_category},  # 使用范围
                'templates': {'post_img': old_tpl.post_img}  # 优惠券模板
            }
            template.save()
        else:  # 不存在即创建
            if old_tpl.valid:  # 历史有效则设置 为发放中
                template_status = CouponTemplate.SENDING
            else:
                template_status = CouponTemplate.CANCEL
            template_extras = {
                'release': {
                    'use_min_payment': old_tpl.use_fee,  # 满多少可以使用
                    'release_min_payment': old_tpl.release_fee,  # 满多少可以发放
                    'use_after_release_days': 0,  # 发放多少天后可用
                    'limit_after_release_days': 0,  # 发放多少天内可用
                    'share_times_limit': 20  # 分享链接被成功领取的优惠券次数
                },
                'randoms': {'min_val': 0, 'max_val': 1},  # 随机金额范围
                'scopes': {'product_ids': old_tpl.bind_pros, 'category_ids': old_tpl.use_pro_category},  # 使用范围
                'templates': {'post_img': old_tpl.post_img}  # 优惠券模板
            }
            template = CouponTemplate(
                id=old_tpl.id,
                title=old_tpl.title,
                description=old_tpl.use_notice,
                value=old_tpl.value,
                prepare_release_num=old_tpl.nums,
                release_start_time=old_tpl.release_start_time,
                release_end_time=old_tpl.release_end_time,
                use_deadline=old_tpl.deadline,
                has_released_count=CPL.objects.filter(template_id=old_tpl.id).count(),
                has_used_count=OUC.objects.filter(cp_id__template_id=old_tpl.id, status=OUC.USED).count(),
                status=template_status,
                extras=template_extras
            )
            template.scope_type = CouponTemplate.SCOPE_OVERALL
            if old_tpl.bind_pros and old_tpl.bind_pros.strip():
                template.scope_type = CouponTemplate.SCOPE_PRODUCT
            if old_tpl.use_pro_category and old_tpl.use_pro_category.strip():
                template.scope_type = CouponTemplate.SCOPE_CATEGORY
            template.save()


from flashsale.pay.models import SaleTrade


def migrate_usercoupon_data():
    """ 用户优惠券数据迁移 """
    old_usercoupons = OUC.objects.all()  # 测试使用10条
    for old_coupon in old_usercoupons:
        try:
            old_tpl = old_coupon.cp_id.template  # 使用的老优惠券模板
        except:
            continue
        tpl = CouponTemplate.objects.get(id=old_tpl.id)
        # 查找现有的优惠券 如果存在则修改 否则添加
        customer_id = old_coupon.customer

        sale_trade = old_coupon.sale_trade.strip()
        if sale_trade and sale_trade != '0' and sale_trade.isdigit():  # 有绑定的交易id
            trade = SaleTrade.objects.filter(id=sale_trade).first()
            trade_tid = trade.tid if trade else ''
            user_coupon = UserCoupon.objects.filter(
                template_id=tpl.id,
                customer_id=old_coupon.customer,  # 指定用户
                trade_tid=trade_tid
            ).first()  # 含有订单的优惠券 单独处理
            if not user_coupon:  # 不存在才创建
                if old_tpl.id in [2, 7, 8, 10]:  # refund 退款补偿的优惠券
                    cou, code, msg = UserCoupon.objects.create_refund_post_coupon(customer_id, tpl.id, trade.id)
                else:
                    try:
                        cou, code, msg = UserCoupon.objects.create_normal_coupon(customer_id, tpl.id)
                        if isinstance(cou, UserCoupon):
                            cou.trade_tid = trade_tid
                            cou.save(update_fields=['trade_tid'])
                    except:
                        logger.warn("tpl:%s, old_coupon:%s,cutomer:%s, sale_trade:%s" % (
                            tpl, old_coupon, customer_id, sale_trade))
                        print(tpl, old_coupon, customer_id, sale_trade)
                        continue
                if old_coupon.status == OUC.USED:  # 使用了
                    if isinstance(cou, UserCoupon):
                        cou.use_coupon(trade.tid)
                elif old_coupon.status == OUC.FREEZE:  # 冻结
                    if isinstance(cou, UserCoupon):
                        cou.freeze_coupon()
        else:
            try:
                cou, code, msg = UserCoupon.objects.create_normal_coupon(customer_id, tpl.id)
                if old_coupon.status == OUC.USED:  # 使用了
                    if isinstance(cou, UserCoupon):
                        logger.warn(u"migrate_usercoupon_data:  cou:%s code:%s msg:%s" % (cou, code, msg))
                elif old_coupon.status == OUC.FREEZE:  # 冻结
                    if isinstance(cou, UserCoupon):
                        cou.freeze_coupon()
            except Exception, exc:
                logger.warn(
                    u'migrate_usercoupon_data: template is %s, customer is %s, old_coupon is %s , except msg :%s' % (
                        tpl.id, customer_id, old_coupon.id, exc.message))
