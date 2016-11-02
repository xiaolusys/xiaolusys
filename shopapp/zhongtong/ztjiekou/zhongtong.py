# -*- coding:utf8 -*-

import json
import time
import hashlib
import base64
import urllib
import urllib2


partner = "test"
pwd = "ZTO123"


# ZTO接口
def handle_demon(data, func):
    # 获取当前日期，对日期进行格式化http://www.sharejs.com/codes/python/8664
    datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

    # 对内容进行进行BASE64编码
    content = base64.b64encode(data)
    # 接口访问测试路径
    url = "http://testpartner.zto.cn/client/interface.php"

    # ZTO接口正式访问路径
    # url="http://partner.zto.cn/client/interface.php"

    # 数据效验码
    verify = hashlib.md5(partner + datetime + content + pwd).hexdigest()

    parmas = {
        'style': 'json',
        'func': func,
        'partner': partner,
        'datetime': datetime,
        'content': content,
        'verify': verify
    }

    date_url = urllib.urlencode(parmas)
    # u = url +'?'+ date_url
    # print 'debug url:',u//get 提交方式
    # request = urllib2.Request(u.decode('utf-8','ignore'))
    request = urllib2.Request(url, date_url)

    response = urllib2.urlopen(request)
    # 参考：http://blog.chinaunix.net/uid-26722078-id-3504625.html
    t = response.read().decode('utf-8')
    print "t ::xxx:: ", type(t), t
    print "json:", type(json.loads(t)), json.loads(t)
    print "========================================="

    return json.loads(t)
