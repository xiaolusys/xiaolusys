# coding=utf-8
import datetime
from django.test import TestCase
from flashsale.coupon.models import CouponTemplate, OrderShareCoupon, UserCoupon
from .apis.v1.usercoupon import create_user_coupon


class CouponTemplateTestCase(TestCase):
    fixtures = [
        'test.flashsale.coupon.customer.json',
        ''
    ]

    def setUp(self):
        release_start_time = datetime.date.today()
        release_end_time = datetime.date.today() + datetime.timedelta(days=5)
        deadline = datetime.date.today() + datetime.timedelta(days=10)
        # 1. 普通优惠券
        # 2. 下单优惠券
        # 3. 分享优惠券
        # 4. 代理邀请优惠券
        # 5. 售后补偿优惠券
        extras1 = {
            'release': {
                'use_min_payment': 500,
                'release_min_payment': 50,
                'use_after_release_days': 0,
                'limit_after_release_days': 30,
                'share_times_limit': 20
            },
            'randoms': {'min_val': 0, 'max_val': 1},
            'scopes': {'product_ids': '', 'category_ids': ''},
            'templates': {'post_img': ''}
        }
        CouponTemplate.objects.create(
            title='test 普通优惠券',
            prepare_release_num=100,
            description='普通优惠券 description',

            is_random_val=False,
            is_flextime=False,

            value=2.0,
            release_start_time=release_start_time,
            release_end_time=release_end_time,
            use_deadline=deadline,

            coupon_type=CouponTemplate.TYPE_NORMAL,
            target_user=CouponTemplate.TARGET_VIP,
            scope_type=CouponTemplate.SCOPE_OVERALL,
            extras=extras1,
            status=CouponTemplate.SENDING
        )
        extras2 = {
            'release': {
                'use_min_payment': 500,
                'release_min_payment': 50,
                'use_after_release_days': 0,
                'limit_after_release_days': 30,
                'share_times_limit': 20
            },
            'randoms': {'min_val': 0, 'max_val': 1},
            'scopes': {'product_ids': '', 'category_ids': ''},
            'templates': {'post_img': ''}
        }
        CouponTemplate.objects.create(
            title='test 下单红包',
            prepare_release_num=100,
            description='下单红包 description',

            is_random_val=False,
            is_flextime=True,

            value=2.0,
            release_start_time=release_start_time,
            release_end_time=release_end_time,
            use_deadline=deadline,

            coupon_type=CouponTemplate.TYPE_ORDER_BENEFIT,
            target_user=CouponTemplate.TARGET_VIP,
            scope_type=CouponTemplate.SCOPE_OVERALL,
            extras=extras2,
            status=CouponTemplate.SENDING
        )

        extras3 = {
            'release': {
                'use_min_payment': 500,
                'release_min_payment': 50,
                'use_after_release_days': 0,
                'limit_after_release_days': 30,
                'share_times_limit': 20
            },
            'randoms': {'min_val': 4, 'max_val': 8},
            'scopes': {'product_ids': '', 'category_ids': ''},
            'templates': {'post_img': ''}
        }

        CouponTemplate.objects.create(
            title='test 订单分享',
            prepare_release_num=100,
            description='订单分享 description',

            is_random_val=True,
            is_flextime=True,

            value=2.0,
            release_start_time=release_start_time,
            release_end_time=release_end_time,
            use_deadline=deadline,

            coupon_type=CouponTemplate.TYPE_ORDER_SHARE,
            target_user=CouponTemplate.TARGET_VIP,
            scope_type=CouponTemplate.SCOPE_OVERALL,
            extras=extras3,
            status=CouponTemplate.SENDING
        )

        extras4 = {
            'release': {
                'use_min_payment': 500,
                'release_min_payment': 50,
                'use_after_release_days': 0,
                'limit_after_release_days': 30,
                'share_times_limit': 20
            },
            'randoms': {'min_val': 4, 'max_val': 8},
            'scopes': {'product_ids': '', 'category_ids': ''},
            'templates': {'post_img': ''}
        }

        CouponTemplate.objects.create(
            title='test 推荐专享',
            prepare_release_num=100,
            description='推荐专享 description',

            is_random_val=False,
            is_flextime=True,

            value=4.0,
            release_start_time=release_start_time,
            release_end_time=release_end_time,
            use_deadline=deadline,

            coupon_type=CouponTemplate.TYPE_MAMA_INVITE,
            target_user=CouponTemplate.TARGET_VIP,
            scope_type=CouponTemplate.SCOPE_OVERALL,
            extras=extras4,
            status=CouponTemplate.SENDING
        )

        extras5 = {
            'release': {
                'use_min_payment': 500,
                'release_min_payment': 50,
                'use_after_release_days': 0,
                'limit_after_release_days': 30,
                'share_times_limit': 20
            },
            'randoms': {'min_val': 0, 'max_val': 1},
            'scopes': {'product_ids': '', 'category_ids': ''},
            'templates': {'post_img': ''}
        }

        CouponTemplate.objects.create(
            title='test 售后补偿',
            prepare_release_num=100,
            description='售后补偿 description',

            is_random_val=False,
            is_flextime=False,

            value=4.0,
            release_start_time=release_start_time,
            release_end_time=release_end_time,
            use_deadline=deadline,

            coupon_type=CouponTemplate.TYPE_COMPENSATE,
            target_user=CouponTemplate.TARGET_VIP,
            scope_type=CouponTemplate.SCOPE_OVERALL,
            extras=extras5,
            status=CouponTemplate.SENDING
        )

    def test_pick_user_coupon(self):
        tid = 'xd160425571d7dee948ab'
        order_share = OrderShareCoupon.objects.create(
            template_id=3, share_customer=1, uniq_id=tid, release_count=3, has_used_count=2,
            limit_share_count=7, share_start_time=datetime.datetime.now(),
            share_end_time=datetime.datetime.now() + datetime.timedelta(days=4)
        )
        create_user_coupon(15937, 1)
        create_user_coupon(15937, 3, order_share_id=order_share.id)
        create_user_coupon(9, 4, trade_id=333451)
        create_user_coupon(15937, 2, trade_id=333451)
        create_user_coupon(10822, 5, trade_id=42886)

