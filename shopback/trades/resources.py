# __author__ = 'meixqhi'
# # from djangorestframework.resources import ModelResource
# from shopback.trades.serializer import MergeTradetSerializer
# from shopback.trades.forms import ExchangeTradeForm,StatisticMergeOrderForm
# from shopback.trades.models import MergeTrade
# # from core.options.resources import BaseResource
# 
# class TradeResource(ModelResource):
#     """ docstring for TradeResource TradeResource """
# 
#     fields = ('trade','logistics','shippings')
#     exclude = ('url',) 
#     
# 
# class MergeTradeResource(ModelResource):
#     """ docstring for MergeTradeResource """
#     model   = MergeTrade
#     fields = ('id','tid','seller_id','seller_nick','buyer_nick','type','shipping_type',
#               'buyer_message','seller_memo','sys_memo','pay_time','modified'
#               ,'created','consign_time','out_sid','status','sys_status',
#               'receiver_name','logistics','weights','df','dt','yunda_count','success')
#     exclude = ('url',) 
# 
#     
# class OrderPlusResource(ModelResource):
#     """ docstring for TradeResource ModelResource """
# 
#     exclude = ('url',) 
#     
# class ExchangeOrderResource(ModelResource):
#     """ docstring for ExchangeOrderResource ModelResource """
#     
#     fields = ('origin_no','trade_type','trade','sellers')
#     form    = ExchangeTradeForm
#     exclude = ('url',) 
#     
# class StatisticMergeOrderResource(ModelResource):
#     """ docstring for StatisticMergeOrderResource ModelResource """
#     
#     model   = MergeTrade
#     form    = StatisticMergeOrderForm
#     exclude = ('url',) 
#     
#     
#
