import json
import urllib
import urllib2


def send(msg,access_token=''):
    
    url = "https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=%s"%access_token
    params = {
        "touser":"oMt59uJJBoNRC7Fdv1b5XiOAngdU",
        "msgtype":"text",
        "text":
            {
            "content":msg
            }
        }
    req  = urllib2.urlopen(url,json.dumps(params))
    resp = req.read()
    print 'debug resp:',resp
    return resp
