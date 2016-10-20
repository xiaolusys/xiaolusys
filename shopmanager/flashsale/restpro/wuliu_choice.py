# -*- coding:utf-8 -*-
from tasks import kdn_sub
from .kdn_wuliu_extra import format_content
import logging

logger = logging.getLogger(__name__)

def one_tradewuliu(logistics_company,out_sid,tradewuliu):
    logger.warn({'action': "kdn", 'info': "one_tradewuliu"})
    exp_status = {0:u"无轨迹",1:u"已揽件",2:u"在途中",
              201:u"到达派件城市",3:u"签收",4:u"已签收",5:u"拒收、用户拒签",6:u"疑难件、以为某些原因无法进行派送",
                  7:u"无效单",8:u"超时单",9:u"签收失败"}
    if tradewuliu.content.find("AcceptTime") == -1:
        kdn_sub.delay(rid=None, expName=logistics_company, expNo=out_sid)
        return "请再次刷新下"
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
    kdn_sub.delay(rid=None, expName=logistics_company, expNo=out_sid)
    return format_content(**format_exp_info)

def zero_tradewuliu(logistics_company,out_sid,tradewuliu):
    logger.warn({'action': "kdn", 'info': "zero_tradewuliu"})
    wuliu_info = {"expName": logistics_company, "expNo": out_sid}
    kdn_sub.delay(rid=None, expName=logistics_company, expNo=out_sid)
    return "物流信息暂未获得"

result_choice = {1:one_tradewuliu,0:zero_tradewuliu}