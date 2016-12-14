# coding=utf-8
from __future__ import absolute_import, unicode_literals
import datetime
from shopmanager import celery_app as app
from django.db import IntegrityError, transaction
from django.template import Context, Template
import logging

logger = logging.getLogger(__name__)


@app.task()
def task_send_transfer_coupons(customer_id, order_id, order_oid, order_num, product_id):
    # type: (int, int, text_type, int, int) -> None
    """创建精品券记录　和　优惠券记录
    """
    from flashsale.pay.apis.v1.customer import get_customer_by_id
    from shopback.items.models import Product
    from flashsale.pay.models import ModelProduct
    from flashsale.coupon.models import CouponTransferRecord
    from ..apis.v1.usercoupon import create_user_coupon
    from ..apis.v1.coupontemplate import get_coupon_template_by_id
    from .coupontemplate import task_update_tpl_released_coupon_nums
    from flashsale.xiaolumm.tasks.tasks_mama_dailystats import task_calc_xlmm_elite_score
    from ..apis.v1.transfercoupondetail import create_transfer_coupon_detail

    customer = get_customer_by_id(customer_id)
    product = Product.objects.filter(id=product_id).first()
    model_product = ModelProduct.objects.filter(id=product.model_id).first()
    template_id = model_product.extras.get("template_id")

    template = get_coupon_template_by_id(id=template_id)
    index = 0
    with transaction.atomic():
        new_coupon_ids = []
        while index < order_num:
            unique_key = template.gen_usercoupon_unikey(order_id, index)
            try:
                cou, code, msg = create_user_coupon(customer.id, template.id, unique_key=unique_key)
                new_coupon_ids.append(cou.id)
            except IntegrityError as e:
                logging.error(e)
            index += 1

        to_mama = customer.get_charged_mama()
        to_mama_nick = customer.nick
        to_mama_thumbnail = customer.thumbnail

        coupon_to_mama_id = to_mama.id
        init_from_mama_id = to_mama.id

        coupon_from_mama_id = 0
        from_mama_thumbnail = 'http://7xogkj.com2.z0.glb.qiniucdn.com/222-ohmydeer.png?imageMogr2/thumbnail/60/format/png'
        from_mama_nick = 'SYSTEM'

        transfer_type = CouponTransferRecord.IN_BUY_COUPON
        date_field = datetime.date.today()
        transfer_status = CouponTransferRecord.DELIVERED
        uni_key = "%s-%s" % (to_mama.id, order_id)
        coupon_value = int(template.value)
        product_img = template.extras.get("product_img") or ''
        elite_score = product.elite_score * (int(order_num))

        try:
            transfer = CouponTransferRecord(coupon_from_mama_id=coupon_from_mama_id,
                                            from_mama_thumbnail=from_mama_thumbnail,
                                            from_mama_nick=from_mama_nick, coupon_to_mama_id=coupon_to_mama_id,
                                            to_mama_thumbnail=to_mama_thumbnail, to_mama_nick=to_mama_nick,
                                            coupon_value=coupon_value,
                                            init_from_mama_id=init_from_mama_id, order_no=order_oid,
                                            template_id=template_id,
                                            product_img=product_img, coupon_num=order_num, transfer_type=transfer_type,
                                            product_id=product_id, elite_score=elite_score,
                                            uni_key=uni_key, date_field=date_field, transfer_status=transfer_status)
            transfer.save()
            create_transfer_coupon_detail(transfer.id, transfer.transfer_type, new_coupon_ids)  # 创建明细记录
        except IntegrityError as e:
            logging.error(e)
    task_calc_xlmm_elite_score(coupon_to_mama_id)  # 计算妈妈积分
    task_update_tpl_released_coupon_nums.delay(template.id)  # 统计发放数量


def _diff_coupons(mama_id):
    # type: (int) -> List[Dict[*Any]]
    """妈妈流通记录检查不一致的数据输出
    """
    from flashsale.xiaolumm.apis.v1.xiaolumama import get_mama_by_id
    from flashsale.pay.apis.v1.customer import get_customer_by_unionid
    from flashsale.coupon.models import UserCoupon, CouponTransferRecord

    mama = get_mama_by_id(id=mama_id)
    customer = get_customer_by_unionid(unionid=mama.unionid)
    stock_num, in_num, out_num = CouponTransferRecord.get_stock_num(mama_id)  # 流通记录数量
    coupon_count = UserCoupon.objects.filter(customer_id=customer.id,
                                             coupon_type=UserCoupon.TYPE_TRANSFER,
                                             status=UserCoupon.UNUSED).count()  # 优惠券数量
    d = stock_num - coupon_count
    data = []
    if d != 0:
        template_ids = CouponTransferRecord.objects.filter(coupon_to_mama_id=mama_id).values('template_id').distinct()
        for entry in template_ids:
            template_id = entry["template_id"]
            num1 = CouponTransferRecord.get_coupon_stock_num(mama_id, template_id)
            num2 = UserCoupon.objects.filter(customer_id=customer.id,
                                             coupon_type=UserCoupon.TYPE_TRANSFER,
                                             status__in=[UserCoupon.UNUSED,
                                                         UserCoupon.FREEZE], template_id=template_id).count()
            if num1 != num2:
                data.append({'mama_id': mama_id,
                             'customer_id': customer.id,
                             'template_id': template_id,
                             'stock': num1,
                             'coupon_num': num2})
    return data


def _send_msg_ding_talk(msg):
    from common.dingding import DingDingAPI

    tousers = [
        '02401336675559',  # 伍磊
        '01591912287010',  # 林杰
    ]
    dd = DingDingAPI()
    for touser in tousers:
        dd.sendMsg(msg, touser)


@app.task()
def task_check_transfer_coupon_record():
    """定时检查　流通记录　是否有　异常记录　有则发送　钉钉消息给　后台同事
    """
    from flashsale.coupon.models import CouponTransferRecord

    mama_ids = CouponTransferRecord.objects.filter(
        transfer_status=CouponTransferRecord.DELIVERED).values('coupon_to_mama_id').distinct()
    data = ['定时检查流通记录任务--->异常数据:\n']
    t = Template('\n妈妈id  :{{mama_id}}\n'
                 '客户id  :{{customer_id}}\n'
                 '模板id  :{{template_id}}\n'
                 '流通存量 :{{stock}}\n'
                 '券数量   :{{coupon_num}}\n'
                 )
    for entry in mama_ids:
        mama_id = entry["coupon_to_mama_id"]
        if mama_id == 0:
            continue
        items = _diff_coupons(mama_id=mama_id)
        for item in items:
            c = Context(item)
            x = t.render(c)
            data.append(x)
    if len(data) == 1:
        return
    msg = '--------------'.join(data)
    _send_msg_ding_talk(msg)
