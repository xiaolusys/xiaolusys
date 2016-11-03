# -*- coding:utf8 -*-
import time
import datetime
import calendar
import json
from celery.exceptions import RetryTaskError
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from django.db.models import Q, F
from shopback import paramconfig as pcfg
from shopapp.notify.models import TradeNotify, ItemNotify, RefundNotify
from shopback.orders.models import Trade, Order
from shopback.trades.models import MergeTrade, MergeOrder, MergeBuyerTrade
from shopback.items.models import Product, ProductSku, Item
from shopback.refunds.models import Refund
from shopback.users.models import User
from shopback.signals import rule_signal
from shopapp.signals import modify_fee_signal
from common.utils import update_model_fields
import logging

logger = logging.getLogger('django.request')


class EmptyMemo(Exception):
    # for memo empty exception
    def __init__(self, msg=''):
        self.msg = msg

    def __str__(self):
        return self.msg


############################ 订单主动消息处理  ###############################
@task(max_retries=3)
def process_trade_notify_task(id):
    """ 处理交易主动通知信息 """
    try:
        notify = TradeNotify.objects.get(id=id)
        # 如果是分销部分订单，主动通知不做处理
        if notify.type != pcfg.FENXIAO_TYPE:

            # 订单创建，修改，关闭，则重新下载该订单，并对订单价格进行修改
            if notify.status in ('TradeCreate', 'TradeCloseAndModifyDetailOrder'):
                if (notify.type != pcfg.COD_TYPE and
                        MergeTrade.judge_need_pull(notify.tid, notify.modified)):
                    response = apis.taobao_trade_get(tid=notify.tid, tb_user_id=notify.user_id)
                    trade_dict = response['trade_get_response']['trade']
                    trade_modify = datetime.datetime.strptime(trade_dict['modified'], '%Y-%m-%d %H:%M:%S')
                    if MergeTrade.judge_need_pull(notify.tid, trade_modify):
                        trade = Trade.save_trade_through_dict(notify.user_id, trade_dict)
                # 货到付款处理
                elif notify.type == pcfg.COD_TYPE:
                    response = apis.taobao_trade_fullinfo_get(tid=notify.tid, tb_user_id=notify.user_id)
                    trade_dict = response['trade_fullinfo_get_response']['trade']
                    trade = Trade.save_trade_through_dict(notify.user_id, trade_dict)

                if notify.type != pcfg.COD_TYPE:
                    # 修改订单价格
                    modify_fee_signal.send(sender='modify_post_fee', user_id=notify.user_id, trade_id=notify.tid)
            # 修改交易备注
            elif notify.status == 'TradeMemoModified':
                try:
                    trade = MergeTrade.objects.get(tid=notify.tid)
                except MergeTrade.DoesNotExist, exc:
                    response = apis.taobao_trade_fullinfo_get(tid=notify.tid, tb_user_id=notify.user_id)
                    trade_dict = response['trade_fullinfo_get_response']['trade']
                    trade = Trade.save_trade_through_dict(notify.user_id, trade_dict)
                else:
                    # 如果交易存在，并且等待卖家发货
                    response = apis.taobao_trade_fullinfo_get(tid=notify.tid,
                                                              fields='tid,buyer_message,seller_memo,seller_flag',
                                                              tb_user_id=notify.user_id)
                    trade_dict = response['trade_fullinfo_get_response']['trade']
                    buyer_message = trade_dict.get('buyer_message', '')
                    seller_memo = trade_dict.get('seller_memo', '')
                    seller_flag = trade_dict.get('seller_flag', 0)

                    # 如果消息没有抓取到，则重试
                    if trade.status in (pcfg.WAIT_BUYER_PAY, pcfg.WAIT_SELLER_SEND_GOODS, pcfg.WAIT_BUYER_CONFIRM_GOODS) \
                            and trade.buyer_message == buyer_message and trade.seller_memo == seller_memo and not seller_memo:
                        raise EmptyMemo('empty memo modified notify:%d' % notify.tid)

                    Trade.objects.filter(id=notify.tid).update(modified=notify.modified,
                                                               buyer_message=buyer_message,
                                                               seller_memo=seller_memo,
                                                               seller_flag=seller_flag)
                    merge_type = MergeBuyerTrade.get_merge_type(trade.tid)
                    trade.modified = notify.modified
                    trade.seller_flag = seller_flag
                    trade.buyer_message = buyer_message

                    if merge_type == 0:
                        trade.seller_memo = seller_memo
                        trade.save()
                    elif merge_type == 2:
                        trade.save()
                        trade.update_seller_memo(notify.tid, seller_memo)
                    elif merge_type == 1:
                        trade.seller_memo = seller_memo
                        try:
                            main_tid = MergeBuyerTrade.objects.get(sub_tid=notify.tid).main_tid
                        except MergeBuyerTrade.DoesNotExist:
                            pass
                        else:
                            main_trade = MergeTrade.objects.get(tid=main_tid)
                            main_trade.update_seller_memo(notify.tid, seller_memo)
                            main_trade.has_memo = True
                            update_model_fields(main_trade, update_fields=['has_memo', ])
                            main_trade.append_reason_code(pcfg.NEW_MEMO_CODE)
                    if trade.seller_memo:
                        trade.has_memo = True
                        update_model_fields(trade, update_fields=['has_memo', 'seller_memo', 'seller_flag', 'modified'])
                        trade.append_reason_code(pcfg.NEW_MEMO_CODE)

            # 交易关闭
            elif notify.status == 'TradeClose':
                Trade.objects.filter(id=notify.tid).update(status=pcfg.TRADE_CLOSED, modified=notify.modified)
                Order.objects.filter(trade=notify.tid).update(status=pcfg.TRADE_CLOSED)
                MergeTrade.objects.filter(tid=notify.tid).update(status=pcfg.TRADE_CLOSED, modified=notify.modified)
                MergeTrade.objects.filter(tid=notify.tid).exclude(sys_status__in=('', pcfg.FINISHED_STATUS)).update(
                    sys_status=pcfg.INVALID_STATUS)
                MergeOrder.objects.filter(tid=notify.tid).update(status=pcfg.TRADE_CLOSED)
                try:
                    merge_trade = MergeTrade.objects.get(tid=notify.tid)
                except:
                    pass
                else:
                    if merge_trade.sys_status == pcfg.INVALID_STATUS and merge_trade.has_merge:
                        merge_order_remover(notify.tid)
            # 买家付款
            elif notify.status == 'TradeBuyerPay':
                response = apis.taobao_trade_fullinfo_get(tid=notify.tid, tb_user_id=notify.user_id)
                trade_dict = response['trade_fullinfo_get_response']['trade']
                trade = Trade.save_trade_through_dict(notify.user_id, trade_dict)
            # 卖家发货
            elif notify.status == 'TradeSellerShip':
                Trade.objects.filter(id=notify.tid).update(status=pcfg.WAIT_BUYER_CONFIRM_GOODS,
                                                           modified=notify.modified, consign_time=notify.modified)
                Order.objects.filter(trade=notify.tid, status=pcfg.WAIT_SELLER_SEND_GOODS).update(
                    status=pcfg.WAIT_BUYER_CONFIRM_GOODS)
                MergeTrade.objects.filter(tid=notify.tid).update(status=pcfg.WAIT_BUYER_CONFIRM_GOODS,
                                                                 modified=notify.modified)
                MergeTrade.objects.filter(tid=notify.tid,
                                          sys_status__in=(pcfg.WAIT_AUDIT_STATUS, pcfg.WAIT_PREPARE_SEND_STATUS,
                                                          pcfg.REGULAR_REMAIN_STATUS), out_sid='').exclude(
                    shipping_type=pcfg.EXTRACT_SHIPPING_TYPE).update(sys_status=pcfg.INVALID_STATUS)
                MergeOrder.objects.filter(tid=notify.tid, status=pcfg.WAIT_SELLER_SEND_GOODS).update(
                    status=pcfg.WAIT_BUYER_CONFIRM_GOODS)
                try:
                    merge_trade = MergeTrade.objects.get(tid=notify.tid)
                except:
                    pass
                else:
                    if merge_trade.sys_status == pcfg.INVALID_STATUS and merge_trade.has_merge:
                        merge_order_remover(notify.tid)

            # 交易成功
            elif notify.status == 'TradeSuccess':
                Trade.objects.filter(id=notify.tid).update(status=pcfg.TRADE_FINISHED, modified=notify.modified)
                Order.objects.filter(trade=notify.tid, status=pcfg.WAIT_BUYER_CONFIRM_GOODS).update(
                    status=pcfg.TRADE_FINISHED)
                MergeTrade.objects.filter(tid=notify.tid).update(status=pcfg.TRADE_FINISHED, modified=notify.modified)
                MergeTrade.objects.filter(tid=notify.tid, sys_status__in=pcfg.WAIT_DELIVERY_STATUS).update(
                    sys_status=pcfg.INVALID_STATUS)
                MergeOrder.objects.filter(tid=notify.tid, status=pcfg.WAIT_BUYER_CONFIRM_GOODS).update(
                    status=pcfg.TRADE_FINISHED)
            # 修改地址
            elif notify.status == 'TradeLogisticsAddressChanged':
                trade = MergeTrade.objects.get(tid=notify.tid)
                response = apis.taobao_logistics_orders_get(tid=notify.tid, tb_user_id=notify.user_id)
                ship_dict = response['logistics_orders_get_response']['shippings']['shipping'][0]
                Logistics.save_logistics_through_dict(notify.user_id, ship_dict)

                trade.append_reason_code(pcfg.ADDR_CHANGE_CODE)
                MergeTrade.objects.filter(tid=notify.tid).update(
                    receiver_name=ship_dict['receiver_name'],
                    receiver_state=ship_dict['receiver_state'],
                    receiver_city=ship_dict['receiver_city'],
                    receiver_district=ship_dict['receiver_district'],
                    receiver_address=ship_dict['receiver_address'],
                    receiver_zip=ship_dict['receiver_zip'],
                    receiver_mobile=ship_dict['receiver_mobile'],
                    receiver_phone=ship_dict['receiver_phone'])

                try:
                    main_tid = MergeBuyerTrade.objects.filter(sub_tid=trade.tid).main_tid
                except:
                    pass
                else:
                    main_trade = MergeTrade.objects.get(tid=main_tid)
                    main_trade.append_reason_code(pcfg.ADDR_CHANGE_CODE)

    except Exception, exc:
        raise process_trade_notify_task.retry(exc=exc, countdown=60)
    else:
        notify.is_exec = True
        notify.save()


############################ 商品主动消息处理  ###############################
@task(max_retries=5)
def process_item_notify_task(id):
    """商品主动消息处理"""
    try:
        notify = ItemNotify.objects.get(id=id)
        if notify.status == "ItemAdd":
            Item.get_or_create(notify.user_id, notify.num_iid, force_update=True)
        elif notify.status == "ItemUpdate":
            item = Item.get_or_create(notify.user_id, notify.num_iid, force_update=True)
            outer_id = item.outer_id
            if outer_id:
                prod = Product.objects.get(outer_id=outer_id)

                from shopback.items.tasks import updateUserProductSkuTask
                updateUserProductSkuTask(user_id=notify.user_id, outer_ids=[outer_id],
                                         force_update_num=False)  # 线上库存修改覆盖系统库存

                item_sku_outer_ids = set()
                items = Item.objects.filter(outer_id=outer_id)
                for item in items:
                    sku_dict = json.loads(item.skus or '{}')
                    if sku_dict:
                        sku_list = sku_dict.get('sku')
                        item_sku_outer_ids.update([sku.get('outer_id', '') for sku in sku_list])
                prod.prod_skus.exclude(outer_id__in=item_sku_outer_ids).update(status=pcfg.REMAIN)

        elif notify.status == "ItemUpshelf":
            item = Item.get_or_create(notify.user_id, notify.num_iid, force_update=True)
            Product.objects.filter(outer_id=item.outer_id).update(status=pcfg.NORMAL)
        elif notify.status == "ItemDownshelf":
            Item.get_or_create(notify.user_id, notify.num_iid, force_update=True)
        elif notify.status == "ItemDelete":
            Item.get_or_create(notify.user_id, notify.num_iid, force_update=True)

    except Exception, exc:
        raise process_item_notify_task.retry(exc=exc, countdown=60)
    else:
        notify.is_exec = True
        notify.save()


############################ 退款主动消息处理  ###############################
@task(max_retries=5)
def process_refund_notify_task(id):
    """
    退款处理
    """
    try:
        notify = RefundNotify.objects.get(id=id)
        # 只处理非分销订单
        try:
            merge_trade = MergeTrade.objects.get(tid=notify.tid)
        except MergeTrade.DoesNotExist:
            pass
        else:
            if merge_trade.type != pcfg.FENXIAO_TYPE:
                if notify.status == 'RefundCreated':
                    refund = Refund.get_or_create(notify.user_id, notify.rid, force_update=True)
                    merge_trade.append_reason_code(pcfg.WAITING_REFUND_CODE)
                    Order.objects.filter(oid=notify.oid, trade=notify.tid).update(status=pcfg.REFUND_WAIT_SELLER_AGREE)
                    order = MergeOrder.objects.get(tid=notify.tid, oid=notify.oid)
                    order.refund_id = notify.rid
                    order.refund_status = pcfg.REFUND_WAIT_SELLER_AGREE
                    # 买家申请退款后订单状态变化,如果有申请退货，退款金额等于订单金额，订单状态在等待卖家发货，则将订单状态设为无效
                    order_sys_status = pcfg.INVALID_STATUS if refund.has_good_return or (
                    refund.refund_fee == order.payment) or \
                                                              (
                                                              order.status == pcfg.WAIT_SELLER_SEND_GOODS) else pcfg.IN_EFFECT
                    order.sys_status = order_sys_status
                    order.save()

                    merge_type = MergeBuyerTrade.get_merge_type(notify.tid)
                    if merge_type == 0:
                        MergeTrade.objects.filter(tid=notify.tid, sys_status=pcfg.WAIT_PREPARE_SEND_STATUS, out_sid='') \
                            .update(modified=notify.modified, sys_status=pcfg.WAIT_AUDIT_STATUS,
                                    refund_num=F('refund_num') + 1)
                    elif merge_type == 1:
                        main_tid = MergeBuyerTrade.objects.get(sub_tid=notify.tid).main_tid
                        main_trade = MergeTrade.objects.get(tid=main_tid)
                        main_trade.append_reason_code(pcfg.WAITING_REFUND_CODE)
                        try:
                            merge_order = MergeOrder.objects.get(tid=main_tid, oid=notify.oid)
                        except MergeOrder.DoesNotExist:
                            pass
                        else:
                            merge_order.refund_id = notify.rid
                            merge_order.refund_status = pcfg.REFUND_WAIT_SELLER_AGREE
                            merge_order.sys_status = order_sys_status
                            merge_order.save()

                        if main_trade.status == pcfg.WAIT_SELLER_SEND_GOODS:
                            merge_order_remover(main_tid)

                    else:
                        # 拆单
                        if merge_trade.status == pcfg.WAIT_SELLER_SEND_GOODS:
                            merge_order_remover(notify.tid)

                elif notify.status in (
                'RefundClosed', 'RefundSuccess', 'RefundSellerAgreeAgreement', 'RefundSellerRefuseAgreement'):
                    refund = Refund.get_or_create(notify.user_id, notify.rid, force_update=True)

                    if notify.status == 'RefundClosed':
                        refund_status = pcfg.REFUND_CLOSED
                        order_status = pcfg.WAIT_SELLER_SEND_GOODS
                    elif notify.status == 'RefundSuccess':
                        refund_status = pcfg.REFUND_SUCCESS
                        order_status = pcfg.TRADE_CLOSED if refund.has_good_return else pcfg.WAIT_SELLER_SEND_GOODS
                    elif notify.status == 'RefundSellerAgreeAgreement':
                        refund_status = pcfg.REFUND_WAIT_RETURN_GOODS
                        order_status = pcfg.TRADE_CLOSED
                    else:
                        refund_status = pcfg.REFUND_REFUSE_BUYER
                        order_status = pcfg.WAIT_SELLER_SEND_GOODS
                    merge_trade = MergeTrade.objects.get(tid=notify.tid)
                    merge_trade.remove_reason_code(pcfg.WAITING_REFUND_CODE)
                    order = MergeOrder.objects.get(tid=notify.tid, oid=notify.oid)
                    order.refund_status = refund_status
                    order.status = order_status
                    order.save()

                    if notify.status == 'RefundSuccess' and merge_trade.status in \
                            (pcfg.WAIT_SELLER_SEND_GOODS, pcfg.WAIT_BUYER_CONFIRM_GOODS):
                        merge_type = MergeBuyerTrade.get_merge_type(notify.tid)
                        if merge_type == 1:
                            main_tid = MergeBuyerTrade.objects.get(sub_tid=notify.tid).main_tid
                            main_trade = MergeTrade.objects.get(tid=main_tid)
                            main_trade.remove_reason_code(pcfg.WAITING_REFUND_CODE)
                            main_trade.append_reason_code(pcfg.NEW_REFUND_CODE)
                            main_trade.has_refund = False
                            main_trade.save()
                            try:
                                merge_order = MergeOrder.objects.get(tid=main_tid, oid=notify.oid)
                            except MergeOrder.DoesNotExist:
                                pass
                            else:
                                merge_order.refund_status = pcfg.REFUND_SUCCESS
                                merge_order.order_status = order_status
                                merge_order.save()
                            rule_signal.send(sender='payment_rule', trade_id=main_trade.id)

                        real_order_num = merge_trade.merge_orders.filter(gift_type=pcfg.REAL_ORDER_GIT_TYPE) \
                            .exclude(refund_status__in=pcfg.REFUND_APPROVAL_STATUS).count()

                        if real_order_num == 0:
                            merge_trade.merge_orders.exclude(gift_type=pcfg.REAL_ORDER_GIT_TYPE).delete()
                        else:
                            rule_signal.send(sender='payment_rule', trade_id=merge_trade.id)
    except Exception, exc:
        raise process_refund_notify_task.retry(exc=exc, countdown=60)
    else:
        notify.is_exec = True
        notify.save()


############################ 批量下载订单主动消息处理  ###############################
@task(max_retries=3)
def process_trade_interval_notify_task(user_id, update_from=None, update_to=None):
    update_handler = update_from and update_to
    try:
        user = User.objects.get(visitor_id=user_id)
        if not update_handler:
            update_from = user.trade_notify_updated
            dt = datetime.datetime.now()
            update_to = dt if dt.day == update_from.day else \
                datetime.datetime(update_from.year, update_from.month, update_from.day, 23, 59, 59)
            updated = dt if dt.day == update_from.day else \
                datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0)

        nick = user.nick
        update_from = update_from.strftime('%Y-%m-%d %H:%M:%S')
        update_to = update_to.strftime('%Y-%m-%d %H:%M:%S')

        has_next = True
        cur_page = 1

        while has_next:
            response_list = apis.taobao_increment_trades_get(tb_user_id=user_id, nick=nick, page_no=cur_page
                                                             , page_size=settings.TAOBAO_PAGE_SIZE * 2,
                                                             start_modified=update_from, end_modified=update_to)

            total_nums = response_list['increment_trades_get_response']['total_results']
            if total_nums > 0:
                notify_list = response_list['increment_trades_get_response']['notify_trades']['notify_trade']
                for notify in notify_list:
                    TradeNotify.save_and_post_notify(notify)

            cur_nums = cur_page * settings.TAOBAO_PAGE_SIZE * 2
            has_next = cur_nums < total_nums
            cur_page += 1
    except Exception, exc:
        raise process_trade_interval_notify_task.retry(exc=exc, countdown=60)
    else:
        if not update_handler:
            user.trade_notify_updated = updated
            user.save()


############################ 批量下载商品主动消息处理  ###############################
@task(max_retries=3)
def process_item_interval_notify_task(user_id, update_from=None, update_to=None):
    update_handler = update_from and update_to
    try:
        user = User.objects.get(visitor_id=user_id)
        if not update_handler:
            update_from = user.trade_notify_updated
            dt = datetime.datetime.now()
            update_to = dt if dt.day == update_from.day else \
                datetime.datetime(update_from.year, update_from.month, update_from.day, 23, 59, 59)
            updated = dt if dt.day == update_from.day else \
                datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0)

        nick = user.nick
        update_from = update_from.strftime('%Y-%m-%d %H:%M:%S')
        update_to = update_to.strftime('%Y-%m-%d %H:%M:%S')

        has_next = True
        cur_page = 1

        while has_next:
            response_list = apis.taobao_increment_items_get(tb_user_id=user_id, nick=nick, page_no=cur_page
                                                            , page_size=settings.TAOBAO_PAGE_SIZE * 2,
                                                            start_modified=update_from, end_modified=update_to)

            total_nums = response_list['increment_items_get_response']['total_results']
            if total_nums > 0:
                notify_list = response_list['increment_items_get_response']['notify_items']['notify_item']
                for notify in notify_list:
                    ItemNotify.save_and_post_notify(notify)

            cur_nums = cur_page * settings.TAOBAO_PAGE_SIZE * 2
            has_next = cur_nums < total_nums
            cur_page += 1
    except Exception, exc:
        raise process_item_interval_notify_task.retry(exc=exc, countdown=60)
    else:
        if not update_handler:
            user.item_notify_updated = updated
            user.save()


############################ 批量下载退款主动消息处理  ###############################
@task(max_retries=3)
def process_refund_interval_notify_task(user_id, update_from=None, update_to=None):
    update_handler = update_from and update_to
    try:
        user = User.objects.get(visitor_id=user_id)
        if not update_handler:
            update_from = user.trade_notify_updated
            dt = datetime.datetime.now()
            update_to = dt if dt.day == update_from.day else \
                datetime.datetime(update_from.year, update_from.month, update_from.day, 23, 59, 59)
            updated = dt if dt.day == update_from.day else \
                datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0)

        nick = user.nick
        update_from = update_from.strftime('%Y-%m-%d %H:%M:%S')
        update_to = update_to.strftime('%Y-%m-%d %H:%M:%S')

        has_next = True
        cur_page = 1

        while has_next:
            response_list = apis.taobao_increment_refunds_get(tb_user_id=user_id, nick=nick, page_no=cur_page
                                                              , page_size=settings.TAOBAO_PAGE_SIZE * 2,
                                                              start_modified=update_from, end_modified=update_to)

            total_nums = response_list['increment_refunds_get_response']['total_results']
            if total_nums > 0:
                notify_list = response_list['increment_refunds_get_response']['notify_refunds']['notify_refund']
                for notify in notify_list:
                    RefundNotify.save_and_post_notify(notify)

            cur_nums = cur_page * settings.TAOBAO_PAGE_SIZE * 2
            has_next = cur_nums < total_nums
            cur_page += 1
    except Exception, exc:
        raise process_refund_interval_notify_task.retry(exc=exc, countdown=60)
    else:
        if not update_handler:
            user.refund_notify_updated = updated
            user.save()


############################ 增量订单主动消息处理  ###############################
@task
def process_trade_increment_notify_task():
    users = User.objects.all()
    for user in users:
        process_trade_interval_notify_task.delay(user.visitor_id)


############################ 增量商品主动消息处理  ###############################
@task
def process_item_increment_notify_task():
    users = User.objects.all()
    for user in users:
        process_item_interval_notify_task.delay(user.visitor_id)


############################ 增量退款主动消息处理  ###############################
@task
def process_refund_increment_notify_task():
    users = User.objects.all()
    for user in users:
        process_refund_interval_notify_task.delay(user.visitor_id)


############################ 丢失主动消息处理  ###############################
@task
def process_discard_notify_task(begin, end, user_id=None):
    if not user_id:
        user_id = User.objects.all()[0].visitor_id

    sdt = datetime.datetime.fromtimestamp(begin / 1000).strftime('%Y-%m-%d %H:%M:%S')
    edt = datetime.datetime.fromtimestamp(end / 1000).strftime('%Y-%m-%d %H:%M:%S')

    response = apis.taobao_comet_discardinfo_get(start=sdt, end=edt, tb_user_id=user_id)
    discard_info = response['comet_discardinfo_get_response']['discard_info_list']['discard_info']

    for info in discard_info:

        user_id = info['user_id']
        nick = info['nick']
        start = datetime.datetime.fromtimestamp(info['start'] / 1000)
        end = datetime.datetime.fromtimestamp(info['end'] / 1000)
        if start.day != end.day:
            end = datetime.datetime(start.year, start.month, start.day, 23, 59, 59)

        if info['type'] == 'trade':
            process_trade_interval_notify_task.delay(user_id, update_from=start, update_to=end)

        elif info['type'] == 'item':
            process_item_interval_notify_task.delay(user_id, update_from=start, update_to=end)

        elif info['type'] == 'refund':
            process_refund_interval_notify_task.delay(user_id, update_from=start, update_to=end)


@task()
def delete_success_notify_record_task(days):
    # 更新定时提醒订单
    dt = datetime.datetime.now() - datetime.timedelta(days, 0, 0)

    ItemNotify.objects.filter(modified__lt=dt, is_exec=True).delete()

    TradeNotify.objects.filter(modified__lt=dt, is_exec=True).delete()

    RefundNotify.objects.filter(modified__lt=dt, is_exec=True).delete()
