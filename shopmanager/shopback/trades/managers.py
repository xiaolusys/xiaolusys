from django.db import models
from shopback.orders.models import MergeTrade

class MergeManager(object):
    
    @transaction.commit_on_success
    def merge_order_maker(sub_tid,main_tid):
        #合单操作
        
        MergeTrade.objects.filter(tid=main_tid,out_sid='',status=pcfg.WAIT_SELLER_SEND_GOODS)\
                .update(sys_status=pcfg.WAIT_AUDIT_STATUS)
        
        sub_trade      = MergeTrade.objects.get(tid=sub_tid)
        main_merge_trade = MergeTrade.objects.get(tid=main_tid)
        
        payment      = 0
        total_fee    = 0
        discount_fee = 0
        post_fee     = float(sub_trade.post_fee or 0 ) + float(main_merge_trade.post_fee or 0)
        is_reverse_order = main_merge_trade.sys_status in (pcfg.WAIT_CHECK_BARCODE_STATUS,pcfg.WAIT_SCAN_WEIGHT_STATUS)
        for order in sub_trade.merge_orders.all():
            try:
                if order.oid:
                    merge_order,state = MergeOrder.objects.get_or_create(oid=order.oid,merge_trade=main_merge_trade)
                else:
                    merge_order = MergeOrder()
            except:
                merge_order = MergeOrder()
            
            for field in order._meta.fields:
                if field.name not in ('id','tid','merge_trade'):
                    setattr(merge_order,field.name,getattr(order,field.name))
            
            merge_order.merge_trade = main_merge_trade
            merge_order.is_merge    = True
            merge_order.sys_status  = order.sys_status
            merge_order.is_reverse_order = is_reverse_order
            merge_order.save()
            
            if order.sys_status == pcfg.IN_EFFECT:
                payment   += float(order.payment or 0)
                total_fee += float(order.total_fee or 0)
                discount_fee += float(order.discount_fee or 0)
        
        if sub_trade.buyer_message:
            main_merge_trade.update_buyer_message(sub_tid,sub_trade.buyer_message)
            main_merge_trade.append_reason_code(pcfg.NEW_MEMO_CODE)
            
        if sub_trade.seller_memo:
            main_merge_trade.update_seller_memo(sub_tid,sub_trade.seller_memo)
            main_merge_trade.append_reason_code(pcfg.NEW_MEMO_CODE)
            
        MergeTrade.objects.filter(tid=main_tid).update(payment = payment + float(main_merge_trade.payment ),
                                                       total_fee = total_fee + float(main_merge_trade.total_fee ),
                                                       discount_fee = discount_fee + float(main_merge_trade.discount_fee or 0),
                                                       post_fee = post_fee)
        
        MergeBuyerTrade.objects.get_or_create(sub_tid=sub_tid,main_tid=main_tid) 
                
        sub_trade.append_reason_code(pcfg.NEW_MERGE_TRADE_CODE)
        if sub_trade.has_merge:
            MergeBuyerTrade.objects.filter(main_tid=sub_trade.tid).update(main_tid=main_tid)
                                                      
        #判断是否还有订单需要合并,如果没有，则去掉需合单问题编号
        queryset = MergeTrade.get_merge_queryset(main_merge_trade.buyer_nick,main_merge_trade.receiver_name,
                                    main_merge_trade.receiver_mobile or main_merge_trade.receiver_phone)
        if queryset.filter(sys_status__in=(pcfg.WAIT_AUDIT_STATUS,pcfg.REGULAR_REMAIN_STATUS))\
            .exclude(id__in=(sub_trade.id,main_merge_trade.id)).count()==0:
            main_merge_trade.remove_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
            
        sub_trade.remove_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
        
        log_action(main_merge_trade.user.user.id,main_merge_trade,CHANGE,u'订单合并成功（%s,%s）'%(main_tid,sub_tid))
        
        if not main_merge_trade.reason_code and not main_merge_trade.out_sid:
            main_merge_trade.sys_status = pcfg.WAIT_PREPARE_SEND_STATUS
            main_merge_trade.save()
        else:
            main_merge_trade.append_reason_code(pcfg.NEW_MERGE_TRADE_CODE)
        return True
    
    @transaction.commit_on_success
    def merge_order_remover(main_tid):
        #拆单操作
        main_trade = MergeTrade.objects.get(tid=main_tid)
        
        if not main_trade.has_merge:
            return
        
        if main_trade.type == pcfg.TAOBAO_TYPE:
            trade = Trade.objects.get(id=main_tid)
            main_trade.payment    = trade.payment
            main_trade.total_fee  = trade.total_fee
            main_trade.post_fee   = trade.post_fee
            main_trade.adjust_fee = trade.adjust_fee
            main_trade.discount_fee = trade.discount_fee
        elif main_trade.type == pcfg.FENXIAO_TYPE:
            purchase_order = PurchaseOrder.objects.get(id=main_tid)
            main_trade.payment   = purchase_order.distributor_payment
            main_trade.post_fee  = purchase_order.post_fee
            main_trade.total_fee = purchase_order.total_fee
        main_trade.remove_reason_code(pcfg.NEW_MERGE_TRADE_CODE)
        main_trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE) 
        main_trade.has_merge = False
        update_model_fields(main_trade,update_fields=['payment','total_fee','post_fee','adjust_fee','discount_fee','has_merge'])
        
        main_trade.merge_orders.filter(Q(oid=None)|Q(is_merge=True)).delete()
        sub_merges = MergeBuyerTrade.objects.filter(main_tid=main_tid)
        for sub_merge in sub_merges:    
            sub_tid  = sub_merge.sub_tid
            sub_merge_trade = MergeTrade.objects.get(tid=sub_tid)
            sub_merge_trade.remove_reason_code(pcfg.NEW_MERGE_TRADE_CODE)
            sub_merge_trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
            main_trade.remove_buyer_message(sub_tid)
            main_trade.remove_seller_memo(sub_tid)
            MergeTrade.objects.filter(tid=sub_tid).update(sys_status=pcfg.WAIT_AUDIT_STATUS)
            
        MergeBuyerTrade.objects.filter(main_tid=main_tid).delete()
        
        log_action(main_trade.user.user.id,main_trade,CHANGE,u'订单取消合并成功')
        
        rule_signal.send(sender='combose_split_rule',trade_id=main_trade.id)
        rule_signal.send(sender='payment_rule',trade_id=main_trade.id) 
    
    @transaction.commit_on_success
    def drive_merge(trade_id):
        """ 合单驱动程序 """
        
        is_merge_success = False
        main_tid    = None 
        trades      =  []
        
        merge_trade = MergeTrade.objects.get(id=trade_id)
        try:
            if merge_trade.has_merge:
                return is_merge_success,merge_trade.tid
                
            if merge_trade.status != pcfg.WAIT_SELLER_SEND_GOODS:
                return is_merge_success,main_tid
            
            buyer_nick      = merge_trade.buyer_nick               #买家昵称
            receiver_mobile = merge_trade.receiver_mobile          #收货手机
            receiver_name    = merge_trade.receiver_name           #收货人
            receiver_address = merge_trade.receiver_address        #收货地址
            full_address     = merge_trade.buyer_full_address      #详细地址
            scan_merge_trades = MergeTrade.objects.filter(Q(receiver_name=receiver_name,buyer_nick=buyer_nick)
                    |Q(receiver_mobile=receiver_mobile),sys_status__in=(pcfg.WAIT_CHECK_BARCODE_STATUS,pcfg.WAIT_SCAN_WEIGHT_STATUS))
            #如果有可能需合并的订单在待扫描区域，则主动合单程序不执行，手动合单
            if scan_merge_trades.count()>0:
                return is_merge_success,main_tid
            
            wait_refunding   = merge_trade.has_trade_refunding()   #待退款
    
            trades = MergeTrade.objects.filter(buyer_nick=buyer_nick,receiver_name=receiver_name,receiver_address=receiver_address
                                        ,sys_status__in=(pcfg.WAIT_AUDIT_STATUS,pcfg.WAIT_PREPARE_SEND_STATUS,pcfg.REGULAR_REMAIN_STATUS)
                                        ,is_force_wlb=False).order_by('pay_time')        
             
            #如果有已有合并记录，则将现有主订单作为合并主订单                           
            has_merge_trades = trades.filter(has_merge=True)                  
            if has_merge_trades.count()>0:
                main_tid = has_merge_trades[0].tid
    
            #如果入库订单没有待退款，则进行合单操作
            if trades.count()>0 and not wait_refunding:
                #如果没有则将按时间排序的第一符合条件的订单作为主订单
                can_merge = True
                if not main_tid:
                    for t in trades.exclude(id=trade_id):
                        full_refund = MergeTrade.judge_full_refund(t.id)
                        if not full_refund and not t.has_refund and t.buyer_full_address == full_address:
                            main_tid = t.tid
                            break
                        if t.has_refund:
                            can_merge = False
                            break
                            
                if main_tid and can_merge:  
                    #进行合单
                    is_merge_success = merge_order_maker(merge_trade.tid,main_tid)
                    main_trade = MergeTrade.objects.get(tid=main_tid)
                    #合并后金额匹配
                    rule_signal.send(sender='payment_rule',trade_id=main_trade.id)
            #如果入库订单待退款，则将同名的单置放入待审核区域
            elif trades.count()>0 or wait_refunding:
                if main_tid :
                    merge_order_remover(main_tid)
                for t in trades:
                    if t.sys_status == pcfg.WAIT_PREPARE_SEND_STATUS:
                        if t.out_sid == '':
                            t.sys_status=pcfg.WAIT_AUDIT_STATUS
                            t.save()
                    else:
                        t.sys_status=pcfg.WAIT_AUDIT_STATUS
                        t.has_merge=False
                        t.save()
        except Exception,exc:        
            logger.error(exc.message+'-- merge trade fail --',exc_info=True)
            merge_trade.append_reason_code(pcfg.MERGE_TRADE_ERROR_CODE)   
            for trade in trades:
                trade.append_reason_code(pcfg.MERGE_TRADE_ERROR_CODE)
           
        return is_merge_success,main_tid



class MergeTradeManager(models.Manager):
    
    def judge_out_stock(self,trade_id):
        #判断是否有缺货
        is_out_stock = False
        trade = Trade.objects.get(id=trade_id)
        orders = trade.merge_trade_orders.filter(sys_status=pcfg.IN_EFFECT)
        for order in orders:
            is_order_out = False
            if order.outer_sku_id:
                try:
                    product_sku = ProductSku.objects.get(product__outer_id=order.outer_id,outer_id=order.outer_sku_id)    
                except:
                    trade.append_reason_code(pcfg.OUTER_ID_NOT_MAP_CODE)
                    order.is_rule_match=True
                else:
                    is_order_out  |= product_sku.is_out_stock
                    #更新待发数
                    product_sku.update_wait_post_num(order.num)
            elif order.outer_id:
                try:
                    product = Product.objects.get(outer_id=order.outer_id)
                except:
                    trade.append_reason_code(pcfg.OUTER_ID_NOT_MAP_CODE)
                    order.is_rule_match=True
                else:
                    is_order_out |= product.is_out_stock
                    #更新待发数
                    product.update_wait_post_num(order.num)
            
            if not is_order_out:
                #预售关键字匹配        
                for kw in OUT_STOCK_KEYWORD:
                    try:
                        order.sku_properties_name.index(kw)
                    except:
                        pass
                    else:
                        is_order_out = True
                        break
            if is_order_out:
                order.out_stock=True
                order.save()
            is_out_stock |= is_order_out
                
        if not is_out_stock:
            trade.remove_reason_code(pcfg.OUT_GOOD_CODE)
        else:
            trade.append_reason_code(pcfg.OUT_GOOD_CODE)
            
        return is_out_stock

    
    def judge_full_refund(cls,trade_id):
        #更新订单实际商品和退款商品数量，返回退款状态

        merge_trade = cls.objects.get(id=trade_id)  

        refund_approval_num = merge_trade.merge_trade_orders.filter(refund_status__in=pcfg.REFUND_APPROVAL_STATUS
                            ,gift_type=pcfg.REAL_ORDER_GIT_TYPE).exclude(is_merge=True).count()
        total_orders_num  = merge_trade.merge_trade_orders.filter(gift_type=pcfg.REAL_ORDER_GIT_TYPE).exclude(is_merge=True).count()

        if refund_approval_num==total_orders_num:
            return True
        
        return False

    def judge_new_refund(cls,trade_id):
        #判断是否有新退款
        merge_trade = cls.objects.get(id=trade_id)
        refund_orders_num   = merge_trade.merge_trade_orders.filter(gift_type=pcfg.REAL_ORDER_GIT_TYPE)\
            .exclude(Q(is_merge=True)|Q(refund_status=pcfg.NO_REFUND)).count()
        
        if refund_orders_num >merge_trade.refund_num:
            merge_trade.refund_num = refund_orders_num
            update_model_fields(merge_trade,update_fields=['refund_num'])
            
            return True
        return False
        
    def judge_rule_match(cls,trade_id):
        
        #系统设置是否进行规则匹配
        config  = SystemConfig.getconfig()
        if not config.is_rule_auto:
            return False
        
        merge_trade = cls.objects.get(id=trade_id)
        try:
            rule_signal.send(sender='product_rule',trade_id=trade_id)
        except:
            merge_trade.append_reason_code(pcfg.RULE_MATCH_CODE)
            return True
        else:
            return False
        
    def get_merge_queryset(cls,buyer_nick,receiver_name,receiver_mobile):
        
        q = Q(receiver_name=receiver_name,buyer_nick=buyer_nick)
        if receiver_mobile:
            q = q|Q(receiver_mobile=receiver_mobile)|Q(receiver_phone=receiver_mobile)
        
        trades = cls.objects.filter(q)
        
        return trades
        
    def judge_need_merge(cls,trade_id,buyer_nick,receiver_name,receiver_mobile):
        #是否需要合单 
        if not receiver_name:   
            return False  
            
        queryset = cls.get_merge_queryset(buyer_nick,receiver_name,receiver_mobile)
        trades = queryset.exclude(id=trade_id).exclude(
                    sys_status__in=('',pcfg.FINISHED_STATUS,pcfg.INVALID_STATUS))
        is_need_merge = False
        
        if trades.count() > 0:
            for trade in trades:
                trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
            is_need_merge = True

        return is_need_merge
    
    def judge_need_pull(cls,trade_id,modified):
        #judge is need to pull trade from taobao
        need_pull = False
        try:
            obj = cls.objects.get(tid=trade_id)
        except:
            need_pull = True
        else:
            if not obj.modified or obj.modified < modified or not obj.sys_status:
                need_pull = True
        return need_pull

    
 