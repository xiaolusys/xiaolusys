from django.db import models
from shopback.orders.models import MergeTrade

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
 