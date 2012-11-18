#-*- coding:utf8 -*-
#系统内部处理交易类
#再次入库
         
#如过该交易是合并后的子订单，如果有新留言或新退款，则需要将他的状态添加到合并主订单上面，
#并将主订单置为问题单，如果全退，则将子订单的留言备注从主订单删除，并清除合并记录
if merge_trade.sys_status == pcfg.ON_THE_FLY_STATUS:
    merge_buyer_trade = MergeBuyerTrade.objects.get(sub_tid=trade.id)
    main_tid = merge_buyer_trade.main_tid
    main_trade = MergeTrade.objects.get(tid=main_tid)
    #如果有新退款
    if has_new_refund:     
        merge_trade.append_reason_code(pcfg.NEW_REFUND_CODE)
        main_trade.merge_trade_orders.filter(Q(oid__isnull=True)|Q(oid__in=[o.oid for o in trade.trade_orders.all()])).delete()
        if not full_new_refund:
             merge_order_maker(trade.id,main_tid)
        main_trade.append_reason_code(pcfg.NEW_REFUND_CODE)
        rule_signal.send(sender='merge_trade_rule',trade_tid=main_tid)    
    #新留言备注
    elif has_new_memo:
        main_trade.update_seller_memo(trade.id,trade.seller_memo)
        merge_trade.append_reason_code(pcfg.NEW_MEMO_CODE)
        MergeTrade.objects.filter(tid=main_tid,sys_status__in=(pcfg.WAIT_AUDIT_STATUS,pcfg.WAIT_PREPARE_SEND_STATUS))\
            .update(sys_status=pcfg.WAIT_AUDIT_STATUS)
        main_trade.append_reason_code(pcfg.NEW_MEMO_CODE)
else:
    #判断当前单是否是合并主订单
    try:
        MergeBuyerTrade.objects.get(main_tid=trade.id)
    except MergeBuyerTrade.DoesNotExist:
        is_main_trade = False
    except MergeBuyerTrade.MultipleObjectsReturned:
        is_main_trade = True
    else:
        is_main_trade = True
    
    if has_new_refund:
        is_merge_success = False
        #如果主订单全退款，则主订单及子订单全部进入问题单，子订单需重新审批,合并记录全删除
        if full_new_refund and is_main_trade:
            merge_buyer_trades = MergeBuyerTrade.objects.filter(main_tid=trade.id)
            if merge_buyer_trades.count()>1:
                sub_merge_trades = MergeTrade.objects.filter(tid__in=[t.sub_tid for t in merge_buyer_trades]).order_by('-created')
                main_index = 0
                for sub_trade in sub_merge_trades:
                    full_refund = MergeTrade.judge_full_refund(sub_trade.tid,sub_trade.type)
                    main_index += 1
                    if not full_refund:
                        main_trade = sub_trade
                        break
                    
                for sub_trade in sub_merge_trades[main_index:]:
                   is_merge_success |= merge_order_maker(sub_trade.tid,main_trade.tid)
                
                if is_merge_success:    
                    rule_signal.send(sender='merge_trade_rule',trade_tid=main_trade.tid) 
        merge_trade.merge_trade_orders.filter(oid=None).delete()
        merge_trade.append_reason_code(pcfg.NEW_REFUND_CODE)
        rule_signal.send(sender='merge_trade_rule',trade_tid=trade.id)    
    elif has_new_memo:
        merge_trade.append_reason_code(pcfg.NEW_MEMO_CODE)
    else:
        merge_trade.append_reason_code(pcfg.POST_MODIFY_CODE)

if merge_trade.out_sid == '':
    merge_trade.sys_status = pcfg.WAIT_AUDIT_STATUS