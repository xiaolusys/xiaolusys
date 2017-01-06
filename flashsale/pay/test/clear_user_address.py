# coding=utf-8
from flashsale.pay.models import UserAddress
from flashsale.pay.models import SaleTrade
from datetime import datetime, timedelta
import hashlib

print UserAddress.objects.count()


def address_strip():
    for ua in UserAddress.objects.filter(status=UserAddress.NORMAL).order_by('-id'):
        state = ua.clean_strip()
        if state:
            ua.save()

def find_duplicate_address():
    res = {}
    need_delete1 = []
    need_delete2 = []
    for ua in UserAddress.objects.filter(status=UserAddress.NORMAL).order_by('-id'):
        key = '-'.join([str(ua.cus_uid) , ua.receiver_name , ua.receiver_phone , ua.receiver_mobile, ua.receiver_state , ua.receiver_city , ua.receiver_district , ua.receiver_address])
        key = key.strip()
        key = hashlib.sha256(key).hexdigest()
        if key in res:
            print 'repeat:' + str(ua.id) + '|' + str(res[key].id) + '|' + str(res[key].created)
            need_delete1.append(ua.id)
            need_delete2.append(res[key].id)
        else:
            res[key] = ua
    return res, need_delete1, need_delete2

def clear_duplicate_address():
    # 由后往前，清除地址表中的重复地址
    # TODO注意处理外键
    res = {}
    # UserAddress.objects.filter(status=UserAddress.DELETE).delete()
    need_delete = []
    for ua in UserAddress.objects.filter(status=UserAddress.NORMAL).order_by('-id'):
        # key = hashlib.sha256(str(ua.cus_uid) + ua.receiver_name + ua.receiver_mobile + ua.receiver_state + ua.receiver_city + ua.receiver_district + ua.receiver_address).hexdigest()
        key = '-'.join([str(ua.cus_uid) , ua.receiver_name , ua.receiver_phone , ua.receiver_mobile, ua.receiver_state , ua.receiver_city , ua.receiver_district , ua.receiver_address])
        key = key.strip()
        if key in res:
            print 'repeat:' + str(ua.id) + '|' + str(res[key].id) + '|' + str(res[key].created)
            if ua.default and not res[key].default:
                res[key].delete()
                res[key] = ua
            else:
                ua.delete()
        else:
            res[key] = ua
    return res


def set_all_sale_trade_user_address_id():
    print SaleTrade.objects.filter(status__in=[SaleTrade.TRADE_NO_CREATE_PAY,SaleTrade.WAIT_BUYER_PAY,
                                    SaleTrade.WAIT_SELLER_SEND_GOODS,SaleTrade.WAIT_BUYER_CONFIRM_GOODS]).count()
    res = {}
    for ua in UserAddress.objects.order_by('-id'):
        key = '-'.join([str(ua.cus_uid) , str(ua.receiver_name).strip() ,
                        str(ua.receiver_mobile).strip(), str(ua.receiver_state).strip(), str(ua.receiver_city).strip(),
                        str(ua.receiver_district).strip(), str(ua.receiver_address).strip()])
        if key not in res:
            res[key] = ua
    for sale_trade in SaleTrade.objects.filter(status__in=[SaleTrade.TRADE_NO_CREATE_PAY,SaleTrade.WAIT_BUYER_PAY,SaleTrade.WAIT_SELLER_SEND_GOODS,SaleTrade.WAIT_BUYER_CONFIRM_GOODS]):
        ua = sale_trade
        key = '-'.join([str(ua.buyer_id), str(ua.receiver_name).strip(),str(ua.receiver_mobile).strip(), str(ua.receiver_state).strip(),
                        str(ua.receiver_city).strip(), str(ua.receiver_district).strip(), str(ua.receiver_address).strip()])
        print sale_trade.id
        if key in res:
            sale_trade.user_address_id = res[key].id
            print 'aaa'
            sale_trade.save()
        else:
            if UserAddress.objects.filter(cus_uid=sale_trade.buyer_id).exists():
                tmp_user_address = UserAddress.objects.filter(cus_uid=sale_trade.buyer_id).order_by('-id')[0]
                sale_trade.user_address_id = tmp_user_address.id
                print 'bbb'
                sale_trade.save()
            else:
                print 'ccc'

if __name__ == '__main__':
    set_all_sale_trade_user_address_id()