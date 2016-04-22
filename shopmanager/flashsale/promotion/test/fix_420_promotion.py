# coding=utf-8
from flashsale.promotion.models_freesample import ReadPacket, AwardWinner
from shopback.trades.models import MergeTrade, MergeOrder
from flashsale.pay.models_user import BudgetLog
import logging

logger = logging.getLogger(__name__)

from flashsale.pay.models_coupon_new import UserCoupon
from flashsale.pay.models import SaleTrade, SaleOrder, SaleRefund


def delete_customer_active_coupon(customer_id):
    """
    删除用户的活动优惠券
    """
    ucps = UserCoupon.objects.filter(customer=customer_id,
                                     cp_id__template__id=40)  # 卡通浴巾188元 id 40
    # 记录优惠券
    coupon_ids = []
    for ucp in ucps:
        coupon_ids.append(str(ucp.id))
        ucp.cp_id.delete()  # 删除券池数据
        ucp.delete()  # 删除优惠
    return ','.join(coupon_ids)


def get_customer_product_order(customer_id):
    """
    获取用户的浴巾活动的orders
    """
    orders = SaleOrder.objects.filter(sale_trade__buyer_id=customer_id,
                                      payment__lte=1,  # 使用过优惠券的记录
                                      item_id__in=[14501, 14502, 14503, 14504, 14505, 23147],
                                      status__in=[SaleOrder.WAIT_SELLER_SEND_GOODS,  # 已付款
                                                  SaleOrder.WAIT_BUYER_CONFIRM_GOODS,  # 已发货
                                                  SaleOrder.TRADE_BUYER_SIGNED,  # 确认签收
                                                  SaleOrder.TRADE_FINISHED]).order_by('created')  # 交易成功
    return orders

# def get_customer_product_order(customer_id):
#     orders = SaleOrder.objects.filter(sale_trade__buyer_id=customer_id,payment__lte=1,item_id__in=[14501, 14502, 14503, 14504, 14505, 23147],
#                                       status__in=[SaleOrder.WAIT_SELLER_SEND_GOODS,
#                                                   SaleOrder.WAIT_BUYER_CONFIRM_GOODS,
#                                                   SaleOrder.TRADE_BUYER_SIGNED,
#                                                   SaleOrder.TRADE_FINISHED]).order_by('created')
#     return orders


from core.options import log_action, CHANGE, ADDITION, get_systemoa_user


def make_budget_log(order):
    """钱包支付的使用退款到钱包"""
    if order.sale_trade.channel == SaleTrade.BUDGET:  # 退回小鹿钱包
        referal_id = 'order' + str(order.id)
        BudgetLog.objects.create(customer_id=order.sale_trade.buyer_id,
                                 flow_amount=order.payment * 100,
                                 budget_type=BudgetLog.BUDGET_IN,
                                 budget_log_type=BudgetLog.BG_REFUND,
                                 status=BudgetLog.CONFIRMED,
                                 referal_id=referal_id)
        return True
    return False


def make_sale_order_refund(order):
    """
    根据订单生成退款单
    """
    refunds = SaleRefund.objects.filter(order_id=order.id)
    if refunds.exists():
        refund = refunds[0]
        refund.charge = order.sale_trade.charge
        refund.save()
        refund_id = refund.id
        return refund_id
    else:
        return ''
        # else:
        # # is_budget = make_budget_log(order)  # 如果是下来了钱包退回小鹿钱包
        # # if is_budget:
        # #     return ''
        # refund = SaleRefund.objects.create(trade_id=order.sale_trade.id,
        # order_id=order.id,
        # buyer_id=order.sale_trade.buyer_id,
        # item_id=order.item_id,
        #                                        title=order.title,
        #                                        sku_id=order.sku_id,
        #                                        sku_name=order.sku_name,
        #                                        refund_num=order.num,
        #                                        refund_fee=order.payment,
        #                                        mobile=order.sale_trade.receiver_mobile,
        #                                        status=SaleRefund.REFUND_WAIT_SELLER_AGREE)
        #     channel = order.sale_trade.channel
        #     refund.channel = channel
        #     refund.charge = order.sale_trade.charge
        #     refund.save()
        #     action_user = get_systemoa_user()
        #     log_action(action_user, refund, ADDITION, u'活动浴巾作废订单处理')
        #     refund_id = refund.id
        #     return refund_id


def close_merge_trade(tid):
    """
    关闭Mergetrade　到退款关闭状态
    """
    from shopback.trades.models import MergeTrade
    from shopback import paramconfig as pcfg

    try:
        mt = MergeTrade.objects.get(tid=tid)
        mt.status = pcfg.TRADE_CLOSED
        mt.save()
        action_user = get_systemoa_user()
        log_action(action_user, mt, CHANGE, u'作废活动订单,退款关闭')
        trade_id = mt.id
        return trade_id
    except Exception, exc:
        logger.warn(exc)
        return 0


import csv


def record_to_csv(filename, data):
    csvfile = file(filename, 'wb')
    writer = csv.writer(csvfile)
    writer.writerow(['用户id', '中奖状态', 'merge_trade_link', 'sale_trade_link', 'sale_refund_link', '优惠券'])
    writer.writerows(data)
    csvfile.close()


def close_saleorder_by_obsolete_awards():
    """
    2016-4-20
    处理活动中奖的作废的中奖记录关闭SaleOrder
    """
    merge_trade_link = 'http://youni.huyi.so/admin/trades/mergetrade/?id__in={0}'
    sale_trade_link = 'http://youni.huyi.so/admin/pay/saletrade/?id__in={0}'
    sale_refund_link = 'http://youni.huyi.so/admin/pay/salerefund/?id__in={0}'  # 42247,42248

    awards1 = AwardWinner.objects.filter(status=1)  # 已经领取中奖信息
    awards2 = AwardWinner.objects.filter(status=2)  # 已经作废中奖信息

    store_data = []
    for award in awards1:  # 领取的
        customer_id = award.customer_id
        award_status = '已领取'
        s_orders = get_customer_product_order(customer_id)
        if s_orders.count() > 1:  # 如果用户有超过一个的浴巾活动的订单

            sale_trade_ids_1 = []
            refund_ids_1 = []
            sale_order_ids = []
            for order in s_orders[1::]:
                refund_id = make_sale_order_refund(order)
                # order.refund_status = SaleRefund.REFUND_WAIT_SELLER_AGREE
                # order.save()
                # action_user = get_systemoa_user()
                # log_action(action_user.id, order, CHANGE, u'活动浴巾修改该订单到申请退款状态')

                sale_order_ids.append(order.id)
                sale_trade_ids_1.append(str(order.sale_trade.id))
                refund_ids_1.append(str(refund_id))

            # 更新merge
            update_merge_by_sale_order(sale_order_ids)

            store_data.append(
                (
                    str(customer_id),
                    award_status,
                    '',
                    sale_trade_link.format(','.join(sale_trade_ids_1)),
                    sale_refund_link.format(','.join(refund_ids_1)),
                    ''
                )
            )
    record_to_csv('handler_acitve_apply.csv', store_data)

    data = []
    customers = get_customers()
    for customer in customers:  # 已经作废
        customer_id = int(customer)
        award_status = '已作废'
        # 删除该用户所有浴巾活动优惠券（含券池）
        user_coupons = delete_customer_active_coupon(customer_id)
        # 查找该用户所有浴巾活动订单
        orders = get_customer_product_order(customer_id)

        # 生成退款单
        sale_trade_ids = []
        merge_trade_ids = []
        refund_ids = []

        sale_order_ids = []
        for order in orders:
            refund_id = make_sale_order_refund(order)
            # sale_order 切换到退款状态
            order.refund_status = SaleRefund.REFUND_WAIT_SELLER_AGREE
            order.save()

            # MergeOrder.objects.filter(oid=order.oid).update(sys_status=MergeOrder.DELETE)
            # merge_trade = MergeOrder.objects.filter(oid=order.oid).first().merge_trade
            # update_merge_trade_status(merge_trade)

            # action_user = get_systemoa_user()
            # log_action(action_user.id, order, CHANGE, u'活动浴巾修改该订单到申请退款状态')

            # 关闭 Mergetrade
            tid = order.sale_trade.tid
            merge_trade_id = close_merge_trade(tid)

            sale_trade_ids.append(str(order.sale_trade.id))
            merge_trade_ids.append(str(merge_trade_id))
            refund_ids.append(str(refund_id))
            sale_order_ids.append(order.id)

        update_merge_by_sale_order(sale_order_ids)

        data.append(
            (
                str(customer_id),
                award_status,
                merge_trade_link.format(','.join(merge_trade_ids)),
                sale_trade_link.format(','.join(sale_trade_ids)),
                sale_refund_link.format(','.join(refund_ids)),
                user_coupons
            )
        )
    record_to_csv('handler_obsolete_apply.csv', data)


def update_merge_trade_status(merge_trade):
    if MergeOrder.NORMAL not in [m.sys_status for m in MergeOrder.objects.filter(merge_trade_id=merge_trade.id)]:
        merge_trade.sys_status = MergeTrade.INVALID_STATUS
        merge_trade.save()


def get_sale_order_ids():
    res = []
    awards1 = AwardWinner.objects.filter(status=1)  # 已经领取中奖信息
    awards2 = get_customers()  # 已经作废中奖信息
    for award in awards1:  # 领取的
        customer_id = award.customer_id
        s_orders = get_customer_product_order(customer_id)
        for s in s_orders:
            res.append(s.id)
    for customer_id in awards2:
        s_orders = get_customer_product_order(customer_id)
        for s in s_orders:
            res.append(s.id)
    return res


def update_merge_by_sale_order(sale_order_ids):
    for sale_order_id in sale_order_ids:
        order = SaleOrder.objects.get(id=sale_order_id)
        if order.refund_status != 0:
            MergeOrder.objects.filter(oid=order.oid).update(sys_status=MergeOrder.DELETE)
            merge_trade = MergeOrder.objects.filter(oid=order.oid).first().merge_trade
            update_merge_trade_status(merge_trade)
    return


update_merge_by_sale_order(['363835'])


def get_customers():
    a = ['808889',
         '823655',
         '852203',
         '805947',
         '120072',
         '799136',
         '720569',
         '793111',
         '820187',
         '796981',
         '865305',
         '803807',
         '801999',
         '808056',
         '865453',
         '825448',
         '815107',
         '826107',
         '865744',
         '826364',
         '854065',
         '866207',
         '865451',
         '806212',
         '861920',
         '819638',
         '806807',
         '821502',
         '785206',
         '824827',
         '803197',
         '802070',
         '418411',
         '797746',
         '866680',
         '867477',
         '849308',
         '809604',
         '783603',
         '806503',
         '786516',
         '865812',
         '823187',
         '803260',
         '739017',
         '849745',
         '684947',
         '788230',
         '465924',
         '832198',
         '801245',
         '159967',
         '824475',
         '865797',
         '794921',
         '867321',
         '824060',
         '802219',
         '803301',
         '866346',
         '865767',
         '818931',
         '868060',
         '866256',
         '823957',
         '827028',
         '798610',
         '841129',
         '869086',
         '867795',
         '865101',
         '868657',
         '865523',
         '801834',
         '806574',
         '794196',
         '868499',
         '866818',
         '867974',
         '867567',
         '826507',
         '867914',
         '808287',
         '869826',
         '800704',
         '860579',
         '821952',
         '869984',
         '807651',
         '869446',
         '789245',
         '865190',
         '848667',
         '601204',
         '480360',
         '866665',
         '795685',
         '869654',
         '797942',
         '869488',
         '870372',
         '784658',
         '866588',
         '819812',
         '839672',
         '785819',
         '870463',
         '797883',
         '869853',
         '256519',
         '869403',
         '868414',
         '788305',
         '865359',
         '868369',
         '870858',
         '865328',
         '802267',
         '870033',
         '825036',
         '783668',
         '871488',
         '846063',
         '806134',
         '866350',
         '870368',
         '868557',
         '825164',
         '867887',
         '413258',
         '844680',
         '810826',
         '870780',
         '159593',
         '871773',
         '800305',
         '872180',
         '814526',
         '397189',
         '872425',
         '806451',
         '871104',
         '872684',
         '802162',
         '870697',
         '871491',
         '872809',
         '784889',
         '820943',
         '842121',
         '823558',
         '872794',
         '803907',
         '871641',
         '872721',
         '873015',
         '872861',
         '786264',
         '459',
         '805789',
         '872023',
         '872901',
         '872927',
         '872735',
         '873434',
         '873265',
         '872980',
         '873702',
         '873712',
         '872492',
         '808779',
         '796050',
         '869917',
         '872842',
         '874164',
         '797972',
         '871531',
         '871794',
         '872131',
         '873981',
         '874135',
         '872806',
         '866414',
         '798864',
         '833540',
         '874847',
         '810807',
         '829050',
         '874543',
         '875767',
         '807837',
         '875193',
         '866742',
         '804949',
         '872467',
         '818219',
         '828656',
         '873720',
         '816306',
         '865276',
         '786432',
         '840942',
         '874128',
         '821231',
         '875987',
         '874388',
         '874646',
         '208253',
         '872984',
         '867692',
         '873906',
         '875235',
         '872175',
         '871607',
         '871463',
         '872664',
         '798969',
         '800415',
         '797937',
         '854468',
         '871091',
         '796383',
         '833603',
         '874629',
         '876136',
         '865533',
         '798157',
         '877268',
         '875617',
         '828989',
         '871027',
         '875211',
         '814713',
         '829581',
         '870794',
         '848105',
         '844518',
         '877644',
         '874800',
         '873812',
         '444978',
         '872672',
         '865746',
         '877319',
         '820085',
         '879195',
         '878666',
         '875539',
         '875089',
         '166795',
         '873043',
         '875113',
         '7277',
         '804898',
         '878849',
         '878022',
         '805314',
         '812860',
         '848885',
         '818749',
         '879563',
         '880503',
         '653440',
         '875599',
         '835655',
         '870255',
         '842206',
         '871661',
         '340209',
         '828237',
         '806298',
         '871895',
         '870736',
         '849163',
         '880972',
         '871721',
         '870293',
         '821250',
         '864938',
         '866470',
         '881006',
         '880923',
         '880940',
         '871369',
         '821456',
         '881324',
         '877260',
         '805557',
         '287412',
         '872998',
         '869623',
         '879366',
         '880329',
         '879576',
         '877485',
         '880365',
         '879868',
         '833733',
         '807407',
         '871654',
         '880500',
         '880992',
         '849997',
         '853205',
         '878887',
         '853707',
         '871916',
         '879911',
         '881854',
         '869828',
         '880987',
         '869049',
         '827249',
         '825248',
         '820464',
         '843990',
         '785948',
         '806550',
         '788077',
         '821075',
         '880084',
         '541477',
         '872823',
         '875537',
         '794800',
         '880959',
         '869921',
         '613070',
         '869356',
         '870873',
         '806083',
         '874819',
         '850541',
         '802520',
         '817782',
         '884587',
         '882795',
         '819755',
         '881068',
         '871014',
         '792348',
         '877603',
         '882713',
         '863982',
         '795120',
         '882000',
         '880366',
         '872817',
         '872710',
         '873326',
         '872908',
         '74393',
         '454',
         '868638',
         '886246',
         '799047',
         '807696',
         '805773']
    return a
