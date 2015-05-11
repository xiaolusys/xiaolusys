#-*- coding:utf8 -*-
import json
import urllib,urllib2

BADU_KD100_URL = "http://baidu.kuaidi100.com/query"
BAIDU_POST_CODE_EXCHANGE={
                         'YUNDA':'yunda',
                         'STO':'shentong',
                         'EMS':'ems',
                         'ZTO':'zhongtong',
                         'ZJS':'zhaijisong',
                         'SF':'shunfeng',
                         'YTO':'yuantong',
                         'HTKY':'huitongkuaidi',
                         'TTKDEX':'tiantian',
                         'QFKD':'quanfengkuaidi',
                         }
POST_CODE_NAME_MAP = {'YUNDA':u'韵达快递',
                      'STO':u'申通快递',
                      'EMS':u'邮政EMS',
                      'ZTO':u'中通快递',
                      'ZJS':u'宅急送',
                      'SF':u'顺丰速运',
                      'YTO':u'圆通',
                      'HTKY':u'汇通快递',
                      'TTKDEX':u'天天快递',
                      'QFKD':u'全峰快递',
                      }

def getLogisticTrace(out_sid,exType):
    
    post_array = []
    post_array.append((u'快递公司', POST_CODE_NAME_MAP.get(exType,'other')))
    post_array.append((u'快递单号', out_sid))
    
    if exType not in POST_CODE_NAME_MAP.keys():
        post_array.append(('运输信息',[('','暂时无法查询该快递公司')]))
        return post_array
    
    data = {'type':BAIDU_POST_CODE_EXCHANGE.get(exType),'postid':out_sid}
    req = urllib2.urlopen(BADU_KD100_URL, urllib.urlencode(data),timeout=30)
    content = json.loads(req.read())
    
    if content.get('message') != 'ok':
        post_array.append(('运输信息',[('','暂未查询到快递信息')]))
        return post_array
    
    traces  = []
    for t in content['data']:
        traces.append((t['ftime'],t['context']))
    post_array.append(('运输信息', traces))
    
    return post_array    
    
    
  
