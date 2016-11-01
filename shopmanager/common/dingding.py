# encoding=utf8
import requests
import simplejson


class DingDingAPI(object):
    """
    1 上海己美网络科技有限公司
    4476238 推广部
    4483290 技术部
    4483291 上海仓库
    4484238 广州仓库
    4486273 供应链
    4495271 用户体验部
    4509199 财务部
    8128918 人事行政部

    """

    corpid = 'dinge323d473d4784329'
    corpsecret = 'k1LS2LMil27fZz81R66qG7U7wwrOJ0RsbaAJUylDFOgOe46TjKtBn0kB4LCMNG25'
    access_token = None

    def __init__(self):
        self.getAccessToken()

    def getAccessToken(self):
        if not self.access_token:
            url = 'https://oapi.dingtalk.com/gettoken'
            params = {
                'corpid': self.corpid,
                'corpsecret': self.corpsecret
            }
            resp = requests.get(url, params=params)
            json = simplejson.loads(resp.content)
            access_token = json.get('access_token', '')
            print access_token
            self.access_token = access_token
        return self.access_token

    def getParty(self):
        url = 'https://oapi.dingtalk.com/department/list?access_token=%s' % self.access_token
        resp = requests.get(url)
        json = simplejson.loads(resp.content)
        return json.get('department')

    def getPartyMember(self, party_id=1):
        url = 'https://oapi.dingtalk.com/user/simplelist'
        params = {
            'access_token': self.access_token,
            'department_id': party_id,
            'offset': 0,
            'size': 100
        }
        resp = requests.get(url, params=params)
        json = simplejson.loads(resp.content)
        return json

    def sendMsg(self, msg, touser=None, toparty=None):
        url = 'https://oapi.dingtalk.com/message/send?access_token=%s' % self.access_token
        headers = {
            'Content-Type': 'application/json'
        }
        params = {
            'touser': touser,
            'toparty': toparty,
            'agentid': '47015836',
            "msgtype": "text",
            "text": {
                "content": msg
            }
        }
        resp = requests.post(url, headers=headers, data=simplejson.dumps(params))
        json = simplejson.loads(resp.content)
        print json


def main():
    dd = DingDingAPI()
    # print dd.getAccessToken()
    # items = dd.getParty()
    # items = dd.getPartyMember(party_id=4483290)
    # print items['hasMore']
    # for item in items['userlist']:
    #     print item['userid'], item['name']

    dd.sendMsg('helldddoa', touser='0550581811782786')
    # dd.sendMsg('', touser='01591912287010')

if __name__ == '__main__':
    main()
