#-*- coding:utf8 -*-
import json
import urllib,urllib2

BADU_KD100_URL = "http://baidu.kuaidi100.com/query"
BAIDU_POST_CODE_EXCHANGE={
                         'YUNDA':'yunda',
                         'STO':'shentong'
                         }
POST_CODE_NAME_MAP = {'YUNDA':u'韵达快递',
                      'STO':u'申通快递'
                      }

def getLogisticTrace(out_sid,exType):
    
    data = {'type':BAIDU_POST_CODE_EXCHANGE.get(exType),'postid':out_sid}
    req = urllib2.urlopen(BADU_KD100_URL, urllib.urlencode(data),timeout=10)
    content = json.loads(req.read())
    
    if content.get('message') != 'ok':
        raise Exception(u'暂未查询到快递信息')
    
    post_array = []
    post_array.append((u'快递公司', POST_CODE_NAME_MAP[exType]))
    post_array.append((u'快递单号', out_sid))
    traces  = []
    for t in content['data']:
        traces.append((t['ftime'],t['context']))
    post_array.append(('运输信息', traces))
    
    return post_array    
    
    
  
