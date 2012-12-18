#-*- coding:utf8 -*-
import time
import datetime
import calendar
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from django.db.models import Q,F
from shopback import paramconfig as pcfg
from shopapp.notify.models import TradeNotify,ItemNotify,RefundNotify
from shopback.orders.models import Trade,Order
from shopback.trades.models import MergeTrade,MergeOrder,MergeBuyerTrade,merge_order_remover
from shopback.items.models import Product,ProductSku,Item
from shopback.refunds.models import Refund
from shopback.users.models import User
from shopapp.signals import modify_fee_signal
from auth import apis
import logging

logger = logging.getLogger('notify.handler')

############################ 订单主动消息处理  ###############################
@task(max_retries=5)    
def process_trade_notify_task(id):
    """ 处理交易主动通知信息 """
    try:
        notify = TradeNotify.objects.get(id=id)
        #订单创建，修改，关闭，则重新下载该订单，并对订单价格进行修改
        if notify.status in ('TradeCreate','TradeCloseAndModifyDetailOrder'):
            if MergeTrade.judge_need_pull(notify.tid,notify.modified):
                response    = apis.taobao_trade_get(tid=notify.tid,tb_user_id=notify.user_id)
                trade_dict  = response['trade_get_response']['trade']
                trade_modify = datetime.datetime.strptime(trade_dict['modified'],'%Y-%m-%d %H:%M:%S')
                if MergeTrade.judge_need_pull(notify.tid,trade_modify):
                    trade = Trade.save_trade_through_dict(notify.user_id,trade_dict)
            #修改订单价格
            modify_fee_signal.send(sender='modify_post_fee',user_id=notify.user_id,trade_id=notify.tid)
        #修改交易备注
        elif notify.status == 'TradeMemoModified':
            try:
                trade = MergeTrade.objects.get(tid=notify.tid)
            except MergeTrade.DoesNotExist,exc:
                response    = apis.taobao_trade_fullinfo_get(tid=notify.tid,tb_user_id=notify.user_id)
                trade_dict  = response['trade_fullinfo_get_response']['trade']
                trade = Trade.save_trade_through_dict(notify.user_id,trade_dict)
            else:
                #如果交易存在，并且等待卖家发货
                if trade.status == pcfg.WAIT_SELLER_SEND_GOODS:
                    response    = apis.taobao_trade_fullinfo_get(tid=notify.tid,fields='tid,seller_memo,seller_flag',tb_user_id=notify.user_id)
                    trade_dict  = response['trade_fullinfo_get_response']['trade']
                    seller_memo  = trade_dict.get('seller_memo','')
                    seller_flag  = trade_dict.get('seller_flag',0)
                    Trade.objects.filter(id=notify.tid).update(modified=notify.modified,seller_memo=seller_memo,seller_flag=seller_flag)
                    MergeTrade.objects.filter(tid=notify.tid).update(modified=notify.modified,seller_memo=seller_memo,seller_flag=seller_flag)
                    #如果是更新了卖家备注，则继续处理，更新旗帜则布处理
                    if seller_memo: 
                        trade.append_reason_code(pcfg.NEW_MEMO_CODE)
                        
                        trades = MergeTrade.objects.filter(buyer_nick=trade.buyer_nick,
                                sys_status__in=(pcfg.WAIT_AUDIT_STATUS,pcfg.WAIT_PREPARE_SEND_STATUS))\
                                                .exclude(tid=trade.id).order_by('-pay_time')
                        merge_buyer_trades = MergeBuyerTrade.objects.filter(main_tid__in=[t.tid for t in trades])
                        #如果有已有合并记录，则将现有主订单作为合并主订单
                        main_tid = None
                        if merge_buyer_trades.count()>0 :
                            main_merge_tid = merge_buyer_trades[0].main_tid
                            main_trade = MergeTrade.objects.get(tid=main_merge_tid)
                            if main_trade.buyer_full_address == trade.buyer_full_address:
                                main_trade.update_seller_memo(trade.tid,trade_dict['seller_memo'])
                                #主订单入问题单
                                MergeTrade.objects.filter(tid=main_merge_tid,out_sid='',sys_status=pcfg.WAIT_PREPARE_SEND_STATUS)\
                                    .update(sys_status=pcfg.WAIT_AUDIT_STATUS)
                        
                        #如果非合并子订单，则入问题单
                        MergeTrade.objects.filter(tid=notify.tid,out_sid='',sys_status = pcfg.WAIT_PREPARE_SEND_STATUS)\
                            .update(sys_status=pcfg.WAIT_AUDIT_STATUS)
       
        #交易关闭
        elif notify.status == 'TradeClose':
            Trade.objects.filter(id=notify.tid).update(status=pcfg.TRADE_CLOSED,modified=notify.modified)
            Order.objects.filter(trade=notify.tid).update(status=pcfg.TRADE_CLOSED)
            MergeTrade.objects.filter(tid=notify.tid).update(status=pcfg.TRADE_CLOSED,modified=notify.modified) 
            MergeTrade.objects.filter(tid=notify.tid,sys_status__in=pcfg.WAIT_DELIVERY_STATUS).update(sys_status=pcfg.INVALID_STATUS) 
            MergeOrder.objects.filter(tid=notify.tid).update(status=pcfg.TRADE_CLOSED)
        #买家付款     
        elif notify.status == 'TradeBuyerPay':
            response    = apis.taobao_trade_fullinfo_get(tid=notify.tid,tb_user_id=notify.user_id)
            trade_dict  = response['trade_fullinfo_get_response']['trade']
            trade = Trade.save_trade_through_dict(notify.user_id,trade_dict)
        #卖家发货    
        elif notify.status == 'TradeSellerShip':
            Trade.objects.filter(id=notify.tid).update(status=pcfg.WAIT_BUYER_CONFIRM_GOODS,modified=notify.modified)
            Order.objects.filter(trade=notify.tid,status=pcfg.WAIT_SELLER_SEND_GOODS).update(status=pcfg.WAIT_BUYER_CONFIRM_GOODS)
            MergeTrade.objects.filter(tid=notify.tid).update(status=pcfg.WAIT_BUYER_CONFIRM_GOODS,modified=notify.modified)
            MergeTrade.objects.filter(tid=notify.tid,sys_status__in=(pcfg.WAIT_AUDIT_STATUS,pcfg.WAIT_PREPARE_SEND_STATUS,
                    pcfg.REGULAR_REMAIN_STATUS)).update(sys_status=pcfg.INVALID_STATUS)
            MergeOrder.objects.filter(tid=notify.tid,status=pcfg.WAIT_SELLER_SEND_GOODS).update(status=pcfg.WAIT_BUYER_CONFIRM_GOODS)            
        #交易成功
        elif notify.status == 'TradeSuccess':
            Trade.objects.filter(id=notify.tid).update(status=pcfg.TRADE_FINISHED,modified=notify.modified)
            Order.objects.filter(trade=notify.tid,status=pcfg.WAIT_BUYER_CONFIRM_GOODS).update(status=pcfg.TRADE_FINISHED)
            MergeTrade.objects.filter(tid=notify.tid).update(status=pcfg.TRADE_FINISHED,modified=notify.modified)
            MergeTrade.objects.filter(tid=notify.tid,sys_status__in=pcfg.WAIT_DELIVERY_STATUS).update(sys_status=pcfg.INVALID_STATUS)
            MergeOrder.objects.filter(tid=notify.tid,status=pcfg.WAIT_BUYER_CONFIRM_GOODS).update(status=pcfg.TRADE_FINISHED)
        #修改地址
        elif notify.status == 'TradeLogisticsAddressChanged':
            trade = MergeTrade.objects.get(tid=notify.tid)
            response    = apis.taobao_logistics_orders_get(tid=notify.tid,tb_user_id=notify.user_id)
            ship_dict  = response['logistics_orders_get_response']['shippings']['shipping'][0]
            Logistics.save_logistics_through_dict(notify.user_id,ship_dict)
            
            trade.append_reason_code(pcfg.ADDR_CHANGE_CODE)
            MergeTrade.objects.filter(tid=notify.tid).update(
                                                            receiver_name  = ship_dict['receiver_name'],
                                                            receiver_state = ship_dict['receiver_state'],
                                                            receiver_city  = ship_dict['receiver_city'],
                                                            receiver_district = ship_dict['receiver_district'],
                                                            receiver_address  = ship_dict['receiver_address'],
                                                            receiver_zip   = ship_dict['receiver_zip'],
                                                            receiver_mobile   = ship_dict['receiver_mobile'],
                                                            receiver_phone = ship_dict['receiver_phone'])
            MergeTrade.objects.filter(tid=notify.tid,out_sid='',sys_statu__in=pcfg.WAIT_DELIVERY_STATUS)\
                .update(sys_status=pcfg.WAIT_AUDIT_STATUS,modified=notify.modified)
            try:
                main_tid = MergeBuyerTrade.objects.filter(sub_tid=trade.tid).main_tid
            except:
                pass
            else:
                main_trade = MergeTrade.objects.get(tid=main_tid)
                main_trade.append_reason_code(pcfg.ADDR_CHANGE_CODE)
                MergeTrade.objects.filter(tid=main_tid,out_sid='',sys_statu__in=pcfg.WAIT_DELIVERY_STATUS)\
                    .update(sys_status=pcfg.WAIT_AUDIT_STATUS)
        
    except Exception,exc:
        logger.error(exc.message,exc_info=True)
        raise process_trade_notify_task.retry(exc=exc,countdown=60)
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
            Item.get_or_create(notify.user_id,notify.num_iid,force_update=True)
        elif notify.status == "ItemUpdate":
            if 'sku' in notify.changed_fields.split(','):
                item = Item.get_or_create(notify.user_id,notify.num_iid,force_update=True)
                response = apis.taobao_item_sku_get(num_iid=notify.num_iid,sku_id=notify.sku_id,tb_user_id=notify.user_id)
                
                sku = response['item_sku_get_response']['sku']
                sku_outer_id = sku.get('outer_id', None)
                
                sku_prop_dict = dict([ ('%s:%s' % (p.split(':')[0], p.split(':')[1]), p.split(':')[3]) for p in sku['properties_name'].split(';') if p])
                
                if item.product:
                    psku, state = ProductSku.objects.get_or_create(outer_id=sku_outer_id, product=item.product)
                    if state:
                        for key, value in sku.iteritems():
                            hasattr(psku, key) and setattr(psku, key, value)
                        psku.prod_outer_id = item.outer_id
                    else:
                        psku.properties_name = sku['properties_name']
                        psku.properties = sku['properties']
                        psku.prod_outer_id = item.outer_id
    
                    properties = ''
                    props = sku['properties'].split(';')
                    prop_dict = item.property_alias_dict
                    for prop in props:
                        if prop :
                            properties += prop_dict.get(prop, '') or sku_prop_dict.get(prop, u'规格有误') 
                            psku.properties_name = properties or psku.properties_values
                    psku.save()

    except Exception,exc:
        logger.error(exc.message,exc_info=True)
        raise process_item_notify_task.retry(exc=exc,countdown=60)
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
        Trade.get_or_create(notify.tid,notify.user_id)
        merge_trade = MergeTrade.objects.get(tid=notify.tid)
        if notify.status == 'RefundCreated':
            refund = Refund.get_or_create(notify.user_id,notify.rid)
            merge_trade.append_reason_code(pcfg.WAITING_REFUND_CODE)
            Order.objects.filter(oid=notify.oid,trade=notify.tid).update(status=pcfg.REFUND_WAIT_SELLER_AGREE)
            MergeOrder.objects.filter(tid=notify.tid,oid=notify.oid).update(refund_id=notify.rid,refund_status=pcfg.REFUND_WAIT_SELLER_AGREE)
            if merge_trade.status == pcfg.WAIT_SELLER_SEND_GOODS:
                merge_type  = MergeBuyerTrade.get_merge_type(notify.tid)
                if merge_type == 0:    
                    MergeTrade.objects.filter(tid=notify.tid,out_sid='')\
                        .update(modified=notify.modified,sys_status=pcfg.WAIT_AUDIT_STATUS,refund_num=F('refund_num')+1)
                elif merge_type == 1:
                    main_tid = MergeBuyerTrade.objects.get(sub_tid=notify.tid).main_tid
                    merge_order_remover(main_tid)
                else:
                    merge_order_remover(notify.tid)

        elif notify.status in('RefundClosed','RefundSuccess','RefundSellerAgreeAgreement','RefundSellerRefuseAgreement'):
            if notify.status == 'RefundClosed':
                refund_status = pcfg.REFUND_CLOSED
                order_status  = pcfg.WAIT_SELLER_SEND_GOODS
            elif notify.status == 'RefundSuccess':
                refund_status = pcfg.REFUND_SUCCESS
                order_status  = pcfg.TRADE_CLOSED
            elif notify.status == 'RefundSellerAgreeAgreement':
                refund_status = pcfg.REFUND_WAIT_RETURN_GOODS
                order_status  = pcfg.TRADE_CLOSED
            else:
                refund_status = pcfg.REFUND_REFUSE_BUYER
                order_status  = pcfg.WAIT_SELLER_SEND_GOODS
            refund = Refund.get_or_create(notify.user_id,notify.rid)
            merge_trade = MergeTrade.objects.get(tid=notify.tid)
            merge_trade.remove_reason_code(pcfg.WAITING_REFUND_CODE)
            MergeOrder.objects.filter(tid=notify.tid,oid=notify.oid).update(refund_status=refund_status,status=order_status)
   
    except Exception,exc:
        logger.error(exc.message,exc_info=True)
        raise process_refund_notify_task.retry(exc=exc,countdown=60)
    else:
        notify.is_exec = True
        notify.save()

############################ 批量下载订单主动消息处理  ###############################
@task(max_retries=3) 
def process_trade_interval_notify_task(user_id,update_from=None,update_to=None):
    
    update_handler = update_from and update_to
    try:
        user = User.objects.get(visitor_id=user_id)
        if not update_handler:
            update_from = user.trade_notify_updated 
            dt = datetime.datetime.now()
            update_to   = dt if dt.day == update_from.day else \
                datetime.datetime(update_from.year,update_from.month,update_from.day,23,59,59)
            updated = dt if dt.day == update_from.day else \
                datetime.datetime(dt.year,dt.month,dt.day,0,0,0)
        
        nick = user.nick
        update_from = update_from.strftime('%Y-%m-%d %H:%M:%S')
        update_to   = update_to.strftime('%Y-%m-%d %H:%M:%S')
        
        has_next = True
        cur_page = 1
        
        while has_next:
            response_list = apis.taobao_increment_trades_get(tb_user_id=user_id,nick=nick,page_no=cur_page
                ,page_size=settings.TAOBAO_PAGE_SIZE*2,start_modified=update_from,end_modified=update_to)
            
            total_nums = response_list['increment_trades_get_response']['total_results']
            if total_nums > 0:
                notify_list = response_list['increment_trades_get_response']['notify_trades']['notify_trade']
                for notify in notify_list:
                    TradeNotify.save_and_post_notify(notify)
    
            cur_nums = cur_page*settings.TAOBAO_PAGE_SIZE*2
            has_next = cur_nums<total_nums
            cur_page += 1
    except Exception,exc:
        logger.error(exc.message or '400',exc_info=True)
        raise process_trade_interval_notify_task.retry(exc=exc,countdown=60)
    else:
        if not update_handler:
            user.trade_notify_updated = updated
            user.save()

############################ 批量下载商品主动消息处理  ###############################
@task(max_retries=3)
def process_item_interval_notify_task(user_id,update_from=None,update_to=None):
    
    update_handler = update_from and update_to
    try:
        user = User.objects.get(visitor_id=user_id)
        if not update_handler:
            update_from = user.trade_notify_updated
            dt = datetime.datetime.now()
            update_to   = dt if dt.day == update_from.day else \
                datetime.datetime(update_from.year,update_from.month,update_from.day,23,59,59)
            updated = dt if dt.day == update_from.day else \
                datetime.datetime(dt.year,dt.month,dt.day,0,0,0)
        
        nick = user.nick
        update_from = update_from.strftime('%Y-%m-%d %H:%M:%S')
        update_to   = update_to.strftime('%Y-%m-%d %H:%M:%S')
        
        has_next = True
        cur_page = 1
        
        while has_next:
            response_list = apis.taobao_increment_items_get(tb_user_id=user_id,nick=nick,page_no=cur_page
                ,page_size=settings.TAOBAO_PAGE_SIZE*2,start_modified=update_from,end_modified=update_to)
            
            total_nums = response_list['increment_items_get_response']['total_results']
            if total_nums > 0:
                notify_list = response_list['increment_items_get_response']['notify_items']['notify_item']
                for notify in notify_list:
                    ItemNotify.save_and_post_notify(notify)
                
            cur_nums = cur_page*settings.TAOBAO_PAGE_SIZE*2
            has_next = cur_nums<total_nums
            cur_page += 1
    except Exception,exc:
        logger.error(exc.message or '400',exc_info=True)
        raise process_item_interval_notify_task.retry(exc=exc,countdown=60)
    else:
        if not update_handler:
            user.item_notify_updated = updated
            user.save()
            

############################ 批量下载退款主动消息处理  ###############################
@task(max_retries=3)
def process_refund_interval_notify_task(user_id,update_from=None,update_to=None):
    
    update_handler = update_from and update_to
    try:
        user = User.objects.get(visitor_id=user_id)
        if not update_handler:
            update_from = user.trade_notify_updated
            dt = datetime.datetime.now()
            update_to   = dt if dt.day == update_from.day else \
                datetime.datetime(update_from.year,update_from.month,update_from.day,23,59,59)
            updated = dt if dt.day == update_from.day else \
                datetime.datetime(dt.year,dt.month,dt.day,0,0,0)
        
        nick = user.nick
        update_from = update_from.strftime('%Y-%m-%d %H:%M:%S')
        update_to   = update_to.strftime('%Y-%m-%d %H:%M:%S')
    
        has_next = True
        cur_page = 1
        
        while has_next:
            response_list = apis.taobao_increment_refunds_get(tb_user_id=user_id,nick=nick,page_no=cur_page
                ,page_size=settings.TAOBAO_PAGE_SIZE*2,start_modified=update_from,end_modified=update_to)
            
            total_nums = response_list['increment_refunds_get_response']['total_results']
            if total_nums > 0:
                notify_list = response_list['increment_refunds_get_response']['notify_refunds']['notify_refund']
                for notify in notify_list:
                    RefundNotify.save_and_post_notify(notify)

            cur_nums = cur_page*settings.TAOBAO_PAGE_SIZE*2
            has_next = cur_nums<total_nums
            cur_page += 1
    except Exception,exc:
        logger.error(exc.message or '400',exc_info=True)
        raise process_refund_interval_notify_task.retry(exc=exc,countdown=60)
    else:
        if not update_handler:
            user.refund_notify_updated = updated
            user.save()
    

############################ 增量订单主动消息处理  ###############################
@task
def process_trade_increment_notify_task():

    users = User.objects.all()
    for user in users:

        process_trade_interval_notify_task.s(user.visitor_id)()
        
        
############################ 增量商品主动消息处理  ###############################
@task
def process_item_increment_notify_task():
    
    users = User.objects.all()
    for user in users:

        process_item_interval_notify_task.s(user.visitor_id)()

############################ 增量退款主动消息处理  ###############################
@task
def process_refund_increment_notify_task():
    
    users = User.objects.all()
    for user in users:

        process_refund_interval_notify_task.s(user.visitor_id)()

############################ 丢失主动消息处理  ###############################
@task
def process_discard_notify_task(begin,end,user_id=None):
    
    if not user_id:
       user_id = User.objects.all()[0].visitor_id
    
    sdt = datetime.datetime.fromtimestamp(begin/1000).strftime('%Y-%m-%d %H:%M:%S')
    edt = datetime.datetime.fromtimestamp(end/1000).strftime('%Y-%m-%d %H:%M:%S')
       
    response = apis.taobao_comet_discardinfo_get(start=sdt,end=edt,tb_user_id=user_id)
    discard_info = response['comet_discardinfo_get_response']['discard_info_list']['discard_info']
    
    for info in discard_info:
        
        user_id  = info['user_id']
        nick     = info['nick']
        start = datetime.datetime.fromtimestamp(info['start']/1000)
        end   = datetime.datetime.fromtimestamp(info['end']/1000)
        if info['type'] == 'trade':
            process_trade_interval_notify_task.s(user_id,update_from=start,update_to=end)()
            
        elif info['type'] == 'item':
            process_item_interval_notify_task.s(user_id,update_from=start,update_to=end)()
            
        elif info['type'] == 'refund':
            process_refund_interval_notify_task.s(user_id,update_from=start,update_to=end)()


@task()
def delete_success_notify_record_task():
    #更新定时提醒订单
    dt = datetime.datetime.now() - datetime.timedelta(1,0,0)
    
    ItemNotify.objects.filter(modified__lt=dt,is_exec=True).delete()
    
    TradeNotify.objects.filter(modified__lt=dt,is_exec=True).delete()
    
    RefundNotify.objects.filter(modified__lt=dt,is_exec=True).delete()
