# -*- coding:utf-8 -*-
from tasks import kdn_sub,kdn_search,kd100_search
from .kdn_wuliu_extra import format_content
from flashsale.restpro import exp_map
import logging
import json
from shopback.trades.models import TradeWuliu,PackageSkuItem

logger = logging.getLogger(__name__)

exp_status = {0: u"无轨迹", 1: u"已揽件", 2: u"在途中",
              201: u"到达派件城市", 3: u"签收", 4: u"问题件", 5: u"拒收、用户拒签", 6: u"疑难件、以为某些原因无法进行派送",
              7: u"无效单", 8: u"超时单", 9: u"签收失败"}


def one_tradewuliu(logistics_company,out_sid,tradewuliu):
    logger.warn({'action': "kdn", 'info': "one_tradewuliu"})
    status = exp_status[tradewuliu.status]
    if not tradewuliu.content:
        fa_time = PackageSkuItem.objects.filter(out_sid=out_sid).first().pay_time
        fa_time = fa_time.strftime('%Y-%m-%d %H:%M:%S')
        content = {}
        content["AcceptTime"] = fa_time
        content['AcceptStation'] = "已出货了哦"
        content2 = []
        content2.append(content)
        content2 = json.dumps(content2)
        tradewuliu.content = content2
    format_exp_info = {
        "status": status,
        "status_code": tradewuliu.status,
        "name": tradewuliu.logistics_company,
        "errcode": tradewuliu.errcode,
        "id": "",
        "message": "",
        "content": tradewuliu.content,
        "out_sid": tradewuliu.out_sid
    }
    if str(logistics_company) in exp_map.kdn_not_support_exp:
        logistics_company = exp_map.kd100_exp_map[str(logistics_company)]
        kd100_search.delay(expName=logistics_company, expNo=out_sid)
    else:
        kdn_sub.delay(rid=None, expName=logistics_company, expNo=out_sid)
    return format_content(**format_exp_info)

def zero_tradewuliu(logistics_company,out_sid,tradewuliu):
    logger.warn({'action': "kdn", 'info': "zero_tradewuliu"+str(logistics_company)})
    wuliu_info = {"expName": logistics_company, "expNo": out_sid}
    if str(logistics_company) in exp_map.kdn_not_support_exp:
        logistics_company = exp_map.kd100_exp_map[str(logistics_company)]
        kd100_search(expName=logistics_company, expNo=out_sid)
    else:
        kdn_sub.delay(rid=None, expName=logistics_company, expNo=out_sid)
        # logistics_company = exp_map.kd100_exp_map[str(logistics_company)]
        # kd100_search(expName=logistics_company, expNo=out_sid)
        kdn_search(rid=None, expName=logistics_company, expNo=out_sid)
    tradewuliu = TradeWuliu.objects.filter(out_sid=out_sid).order_by("-id").first()

    if not tradewuliu:
        fa_time = PackageSkuItem.objects.filter(out_sid=out_sid).first().pay_time
        fa_time = fa_time.strftime('%Y-%m-%d %H:%M:%S')
        content = {}
        content["AcceptTime"] = fa_time
        content['AcceptStation'] = "已出货了哦"
        content2 = []
        content2.append(content)
        content2 = json.dumps(content2)
        format_exp_info = {
            "status": 0,
            "status_code": '',
            "name": logistics_company,
            "errcode": '',
            "id": "",
            "message": "",
            "content": content2,
            "out_sid": out_sid
        }
        return format_content(**format_exp_info)
        return "暂无物流信息"

    status = exp_status[tradewuliu.status]
    format_exp_info = {
        "status": status,
        "status_code": tradewuliu.status,
        "name": tradewuliu.logistics_company,
        "errcode": tradewuliu.errcode,
        "id": "",
        "message": "",
        "content": tradewuliu.content,
        "out_sid": tradewuliu.out_sid
    }
    return format_content(**format_exp_info)

result_choice = {1:one_tradewuliu,0:zero_tradewuliu}