import urllib
import httplib2

base_subway_url = 'http://subway.simba.taobao.com/'

def subway_proxy(api_url,method='GET'):
    """ docstring for subway_proxy apis """
    def _wraper(func):
        """ docstring for _wraper """
        def _wrap(*args,**kwargs):

            headers = {
                'Accept':'application/json, text/javascript, */*',
                'Accept-Charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                'Accept-Encoding':'gzip,deflate,sdch',
                'Accept-Language':'en-US,en;q=0.8',
                'Content-Type':'application/x-www-form-urlencoded',
                'Cookie':kwargs['cookie'],
            }
            params = kwargs['params']
            token = kwargs['token']
            campaignId = kwargs['campaignId']

            url = '%s%s?token=%s&campaignId=%s'%(base_subway_url,api_url,token,campaignId)
            http = httplib2.Http()
            if method=='POST':
                headers, content = http.request(url,'POST',body=urllib.urlencode(params),headers=headers)
            else:
                get_url = '%s?%s'%(url,urllib.urlencode(params))
                headers, content = http.request(get_url,'GET',headers=headers)

            return headers,content

        return _wrap
    return _wraper


@subway_proxy('bidword/queryScore4Words.htm',method='POST')
def bidword_queryScore4Words(token=None,campaignId=None,cookie=None,params={}):
    pass