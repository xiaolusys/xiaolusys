# coding=utf-8
from flashsale.pay.models_addr import UserAddress
from flashsale.pay.models import SaleTrade
from datetime import datetime, timedelta
import hashlib

print UserAddress.objects.count()


def address_strip():
    for ua in UserAddress.objects.filter(status=UserAddress.NORMAL).order_by('-id'):
        state = ua.clean_strip()
        if state:
            ua.save()


def clear_duplicate_address():
    # 由后往前，清除地址表中的重复地址
    # TODO注意处理外键
    res = {}
    UserAddress.objects.filter(status=UserAddress.DELETE).delete()
    for ua in UserAddress.objects.filter(status=UserAddress.NORMAL).order_by('-id'):
        # key = hashlib.sha256(str(ua.cus_uid) + ua.receiver_name + ua.receiver_mobile + ua.receiver_state + ua.receiver_city + ua.receiver_district + ua.receiver_address).hexdigest()
        key = '-'.join([str(ua.cus_uid) , ua.receiver_name , ua.receiver_phone , ua.receiver_mobile, ua.receiver_state , ua.receiver_city , ua.receiver_district , ua.receiver_address])
        key = key.strip()
        if key in res:
            print 'repeat:' + str(ua.id) + '|' + str(res[key].id)
            if ua.default and not res[key].default:
                res[key].delete()
                res[key] = ua
            else:
                ua.delete()
        else:
            res[key] = ua
    return res


def set_all_sale_trade_user_address_id():
    # 为所有未发货未关闭的SaleTrade设置地址表中的id
    # 如果存在这个地址，则直接设置，如果不存在这个地址，则设置未该用户的第一个地址。
    print SaleTrade.objects.filter(status__in=[SaleTrade.TRADE_NO_CREATE_PAY,SaleTrade.WAIT_BUYER_PAY,
                                    SaleTrade.WAIT_SELLER_SEND_GOODS,SaleTrade.WAIT_BUYER_CONFIRM_GOODS]).count()
    res = {}
    for ua in UserAddress.objects.order_by('-id'):
        key = '-'.join([str(ua.cus_uid) , ua.receiver_name , ua.receiver_phone , ua.receiver_mobile, ua.receiver_state , ua.receiver_city , ua.receiver_district , ua.receiver_address])
        if key not in res:
            res[key] = ua
    for sale_trade in SaleTrade.objects.filter(status__in=[SaleTrade.TRADE_NO_CREATE_PAY,SaleTrade.WAIT_BUYER_PAY,
                                                           SaleTrade.WAIT_SELLER_SEND_GOODS,SaleTrade.WAIT_BUYER_CONFIRM_GOODS]):
        ua = sale_trade
        key = '-'.join([str(ua.buyer_id), ua.receiver_name.strip(), ua.receiver_phone.strip(),
                        ua.receiver_mobile.strip(), ua.receiver_state.strip(),
                        ua.receiver_city.strip(), ua.receiver_district.strip(), ua.receiver_address.strip()])
        if key in res:
            sale_trade.user_address_id = res[key].id
            print '可设定'
            sale_trade.save()
        else:
            if UserAddress.objects.filter(cus_uid=sale_trade.buyer_id).exists():
                tmp_user_address = UserAddress.objects.filter(cus_uid=sale_trade.buyer_id).order_by('-id')[0]
                sale_trade.user_address_id = tmp_user_address.id
                print '猜的'
                sale_trade.save()
            else:
                print '不存在于地址表'

if __name__ == '__main__':
    set_all_sale_trade_user_address_id()