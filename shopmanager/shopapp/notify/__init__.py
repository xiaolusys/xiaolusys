# -*- coding:utf8 -*
#        #修改地址
#        elif notify.status == 'TradeLogisticsAddressChanged':
#            trade = MergeTrade.objects.get(tid=notify.tid)
#            response    = apis.taobao_logistics_orders_get(tid=notify.tid,tb_user_id=notify.user_id)
#            ship_dict  = response['logistics_orders_get_response']['shippings']['shipping'][0]
#            Logistics.save_logistics_through_dict(notify.user_id,ship_dict)
#            
#            trade.append_reason_code(pcfg.ADDR_CHANGE_CODE)
#            MergeTrade.objects.filter(tid=notify.tid).update(
#                                                            receiver_name  = ship_dict['receiver_name'],
#                                                            receiver_state = ship_dict['receiver_state'],
#                                                            receiver_city  = ship_dict['receiver_city'],
#                                                            receiver_district = ship_dict['receiver_district'],
#                                                            receiver_address  = ship_dict['receiver_address'],
#                                                            receiver_zip   = ship_dict['receiver_zip'],
#                                                            receiver_mobile   = ship_dict['receiver_mobile'],
#                                                            receiver_phone = ship_dict['receiver_phone'])
#            MergeTrade.objects.filter(tid=notify.tid,out_sid='',sys_statu__in=pcfg.WAIT_DELIVERY_STATUS)\
#                .update(sys_status=pcfg.WAIT_AUDIT_STATUS,modified=notify.modified)
#            try:
#                main_tid = MergeBuyerTrade.objects.filter(sub_tid=trade.tid).main_tid
#            except:
#                pass
#            else:
#                main_trade = MergeTrade.objects.get(tid=main_tid)
#                main_trade.append_reason_code(pcfg.ADDR_CHANGE_CODE)
#                MergeTrade.objects.filter(tid=main_tid,out_sid='',sys_statu__in=pcfg.WAIT_DELIVERY_STATUS)\
#                .update(sys_status=pcfg.WAIT_AUDIT_STATUS)
