#encoding:utf-8
from pyExcelerator import * 
import datetime
import time
import hashlib

import re
reg1 = re.compile('^1[34578][0-9]{9}$')
reg2 = re.compile('^(0[0-9]{2,3}\-)?([2-9][0-9]{6,7})+(\-[0-9]{1,4})?$')

def parse_data(file_path):
    sheets = parse_xls(file_path)
    ds = {}
    for index, sht in enumerate(sheets[0:]):
        print sht[0], len(sht[1].values())
        for k,v in sht[1].iteritems():
            y, x = k
            key = '%s-%s' % (index, y)
            if not key in ds:
                ds[key] = ['', '', '', '', sht[0]]
               
            if not isinstance(v, (unicode, str)):
                v = '%s' % v

            if x == 0:
                ds[key][0] = v.strip() or ''
            
            if x == 2:
                ds[key][1] = v.strip().replace(' ', '').split('.')[0]
                
            if x == 3:
                ds[key][2] = v.strip() or ''

            if x == 4:
                ds[key][3] = v.strip().replace(' ', '').split('.')[0]

    dsv = ds.values() 
    data = []
    mbs = set()

    print 'pre parse count=', len(dsv)

    for vv in dsv:
        mb = vv[1]
        if (reg1.match(mb) or reg2.match(mb)) and vv[3] == '1':
            if mb not in mbs:
                data.append(vv)
                mbs.add(mb)
            else:
                print 'repeat:', vv[4].encode('utf8') ,vv[0].encode('utf8') ,vv[1].encode('utf8') ,vv[2].encode('utf8')
        else:
            if vv[1] and not vv[1][0].isdigit():
                continue
            print vv[4].encode('utf8') ,vv[0].encode('utf8') ,vv[1].encode('utf8') ,vv[2].encode('utf8')

    print 'post parse count=', len(data)
    
    return data
    
def create_package_and_skuitem(order):
    
    from shopback.trades.models import *
    from flashsale.xiaolumm.models import XiaoluMama
    from flashsale.pay.models import Customer, SaleTrade
    from flashsale.xiaolumm.models import ReferalRelationship
    addr = order[2]
    city = ''
    if addr.find('市') > 0:
        start = 2
        if addr.find('省') > 0:
            start = addr.index('省')+1
        city = addr[start:addr.index('市')]
        
    receiver_state = addr[0:2]
    receiver_city  = city
    receiver_district = ''
    receiver_address  = addr
    receiver_name = order[0]
    receiver_mobile = order[1]
    master_name = order[4]
    ware_by = 1

    # 1,检查是否小鹿妈妈; 2, 是否已经创建订单;
    # xlmm = XiaoluMama.objects.filter(mobile=receiver_mobile).first()
    # if not xlmm:
    #     cuser = Customer.objects.filter(mobile=receiver_mobile, status=Customer.NORMAL).first()
    #     xlmm = cuser and cuser.getXiaolumm() or None
    #
    # if not xlmm:
    #     st = SaleTrade.objects.filter(receiver_mobile=receiver_mobile, status__lte=SaleTrade.TRADE_FINISHED).first()
    #     if not st:
    #         raise Exception('还不是小鹿妈妈!')

    # rlship = ReferalRelationship.objects.filter(referal_to_mama_id=xlmm.id).first()
    # if not rlship or rlship.referal_type < XiaoluMama.ELITE:
    #     raise Exception('还不是付费小鹿妈妈!')

    po = PackageOrder.objects.filter(created__gt=datetime.datetime(2018,1,4), receiver_mobile=receiver_mobile).first()
    if po:
        raise Exception('订单已经创建!')

    po = PackageOrder()
    address = addr
    user_address_unikey = hashlib.sha1(address).hexdigest()
    po.action_type = 1
    po.sys_status = PackageOrder.WAIT_PREPARE_SEND_STATUS
    _now = datetime.datetime.now()
    time_s = time.mktime(_now.timetuple())
    po.tid = 'h%s' % time_s
    po.action_type = 1
    po.ware_by = ware_by
    po.sys_status = PO_STATUS.WAIT_PREPARE_SEND_STATUS
    po.sku_num = 1
    po.order_sku_num = 1
    po.seller_id = ShopUser.objects.get(uid=FLASH_SELLER_ID).id
    poid = "%s-%s-%s" % (po.seller_id, receiver_mobile, ware_by)
    po.id = poid + '-2-201801'
    po.receiver_name = receiver_name
    po.receiver_state = receiver_state
    po.receiver_city = receiver_city
    po.receiver_district = receiver_district
    po.receiver_address = receiver_address
    po.receiver_zip = ''
    po.receiver_mobile = receiver_mobile
    po.receiver_phone = ''
    po.user_address_id = ''
    po.buyer_id = None
    po.buyer_nick = '%s-%s'%(master_name, receiver_name)
    po.logistics_company = LogisticsCompany.objects.get(id=-2)
    po.can_send_time = datetime.datetime.now()
    po.save()
    # 试用装 + 黑糖
    psi = PackageSkuItem.create_by_hand(ProductSku.objects.get(id=300134),
                                        1,
                                        po.pid,
                                        po.id,
                                        po.receiver_mobile,
                                        po.ware_by)

    psi = PackageSkuItem.create_by_hand(ProductSku.objects.get(id=295847),
                                        1,
                                        po.pid,
                                        po.id,
                                        po.receiver_mobile,
                                        po.ware_by)


def execute(file_path):
    ds = parse_data(file_path)
    for vv in ds:
        try:
            create_package_and_skuitem(vv)
        except Exception, exc:
            print 'error', vv[4].encode('utf8') ,vv[0].encode('utf8') ,vv[1].encode('utf8') ,vv[2].encode('utf8'), str(exc)
            
