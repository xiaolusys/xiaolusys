#-*- coding:utf8 -*-
#系统内部处理交易类
#再次入库
         
#如过该交易是合并后的子订单，如果有新留言或新退款，则需要将他的状态添加到合并主订单上面，
#并将主订单置为问题单，如果全退，则将子订单的留言备注从主订单删除，并清除合并记录
"""
    #重新下载订单
    def pull_order_action(self, request, queryset):
        queryset = queryset.filter(sys_status=pcfg.WAIT_AUDIT_STATUS)
        
        pull_success_ids = []
        pull_fail_ids    = []
        for trade in queryset:
            try:
                if trade.type == pcfg.TAOBAO_TYPE:
                    response = apis.taobao_trade_fullinfo_get(tid=trade.tid,tb_user_id=trade.seller_id)
                    MergeTrade.objects.filter(tid=trade.tid).delete()
                    trade_dict = response['trade_fullinfo_get_response']['trade']
                    Trade.save_trade_through_dict(trade.seller_id,trade_dict)
                elif trade.type == pcfg.FENXIAO_TYPE:
                    try:
                        Trade.objects.get(id=trade.tid)
                    except Exception,exc:
                        purchase = PurchaseOrder.objects.get(id=trade.tid)
                        response_list = apis.taobao_fenxiao_orders_get(purchase_order_id=purchase.fenxiao_id,tb_user_id=trade.seller_id)
                        MergeTrade.objects.filter(tid=trade.tid).delete()
                        orders_list = response_list['fenxiao_orders_get_response']
                        if orders_list['total_results']>0:
                            o = orders_list['purchase_orders']['purchase_order'][0]
                            PurchaseOrder.save_order_through_dict(trade.seller_id,o)
                    else:
                        response = apis.taobao_trade_fullinfo_get(tid=trade.tid,tb_user_id=trade.seller_id)
                        MergeTrade.objects.filter(tid=trade.tid).delete()
                        trade_dict = response['trade_fullinfo_get_response']['trade']
                        Trade.save_trade_through_dict(trade.seller_id,trade_dict)                          
            except Exception,exc:
                logger.error(exc.message,exc_info=True)
                pull_fail_ids.append(trade.tid)
            else:
                pull_success_ids.append(trade.tid)
        success_trades = MergeTrade.objects.filter(tid__in=pull_success_ids)
        fail_trades    = MergeTrade.objects.filter(tid__in=pull_fail_ids)
        return render_to_response('trades/repullsuccess.html',{'success_trades':success_trades,'fail_trades':fail_trades},
                                  context_instance=RequestContext(request),mimetype="text/html") 

    pull_order_action.short_description = "重新下单".decode('utf8')
"""
