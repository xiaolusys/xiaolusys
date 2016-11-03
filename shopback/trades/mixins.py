# -*- coding: utf-8 -*
from shopback import paramconfig as pcfg
from shopapp.taobao import apis
import logging

logger = logging.getLogger('django.request')


class TaobaoTradeService(object):
    def get_trade_id(self):
        return self.trade.id

    def get_seller_id(self):
        return self.trade.seller_id

    def get_trade_type(self):
        if hasattr(self.trade, 'trade_type'):
            return self.trade.trade_type
        return self.trade.type


class TaobaoSendTradeMixin(object):
    def isTradePostOK(self, out_sid):
        """ 判断淘宝订单是否发货成功 """

        response = apis.taobao_logistics_orders_get(tid=self.trade.id,
                                                    tb_user_id=self.trade.seller_id,
                                                    fields='out_sid,tid')
        trade_dicts = response['logistics_orders_get_response']['shippings']['shipping']
        print 'trade_dicts:', trade_dicts
        if len(trade_dicts) == 0:
            raise Exception(u'订单物流信息未查到')

        taobao_sid = trade_dicts[0].get('out_sid', '')
        if not taobao_sid:
            raise Exception(u'订单未发货')

        if taobao_sid and taobao_sid != out_sid:
            raise Exception(u'系统快递单号与线上发货快递单号不一致')

        return True

    def sendTrade(self, company_code=None, out_sid=None, is_cod=False, retry_times=3, *args, **kwargs):
        """ 订单在淘宝后台发货 """

        trade_id = self.get_trade_id()
        trade_type = self.get_trade_type()
        seller_id = self.get_seller_id()
        company_code = company_code.split('_')[0]

        try:
            # 如果货到付款
            if is_cod:
                response = apis.taobao_logistics_online_send(tid=trade_id, out_sid=out_sid
                                                             , company_code=company_code, tb_user_id=seller_id)
                # response = {'logistics_online_send_response': {'shipping': {'is_success': True}}}
                if not response['logistics_online_send_response']['shipping']['is_success']:
                    raise Exception(u'订单(%d)淘宝发货失败' % trade_id)

            else:
                response = apis.taobao_logistics_offline_send(tid=trade_id, out_sid=out_sid
                                                              , company_code=company_code, tb_user_id=seller_id)
                # response = {'logistics_offline_send_response': {'shipping': {'is_success': True}}}
                if not response['logistics_offline_send_response']['shipping']['is_success']:
                    raise Exception(u'订单(%d)淘宝发货失败' % trade_id)

        except apis.LogisticServiceBO4Exception, exc:
            return self.isTradePostOK(out_sid)

        except apis.LogisticServiceB60Exception, exc:
            from shopback.logistics.models import LogisticsCompany
            company = LogisticsCompany.objects.get(code=company_code)
            self.sendTrade(company_code=u'%s' % company.name, out_sid=out_sid, is_cod=is_cod)

        except Exception, exc:
            retry_times = retry_times - 1
            if retry_times <= 0:
                raise exc

            self.sendTrade(company_code=company_code, out_sid=out_sid, is_cod=is_cod, retry_times=retry_times)

        return True
