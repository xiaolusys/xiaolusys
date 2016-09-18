# -*- coding:utf-8 -*-
from tasks import kdn_sub
from .kdn_wuliu_extra import format_content

def one_tradewuliu(logistics_company,out_sid,tradewuliu):
    status = tradewuliu.get_status_display()
    format_exp_info = {
        "status": status,
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
    wuliu_info = {"expName": logistics_company, "expNo": out_sid}
    kdn_sub.delay(rid=None, expName=logistics_company, expNo=out_sid)
    return "物流信息暂未获得"

result_choice = {1:one_tradewuliu,0:zero_tradewuliu}