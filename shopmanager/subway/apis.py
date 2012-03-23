import urllib
import httplib2

base_subway_url = 'http://subway.simba.taobao.com/'

taoci_url = 'http://cube.data.taobao.com/cubex/proxy/s/db/keywords/fact_cat_top_query_d/'+\
               'get_taoci_hotkeys_rank_detail/param/tfix:200/where/f0:eq:%s/where/r1:ge:%s/'+\
               'where/r1:le:%s/where/cid:eq:%s/param/dtb:cat?'

liangzi_url = 'http://api.linezing.com/=/view/p4p-adv/keyword/detail?limit=%s&offset=0&istop=1&sort=finprice&dir=desc&days=%s..%s'

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


def taoci_proxy(from_date=None,to_date=None,cat_id=None,cookie=None):

    headers = {
                'Accept':'text/plain, */*',
                'Accept-Charset':'en-us,en;q=0.5',
                'Accept-Encoding':'gzip,deflate',
                'Accept-Language':'en-US,en;q=0.8',
                'Connection':'keep-alive',
                'Referer':'http://cube.data.taobao.com/s/key/index',
                'User-Agent':'Mozilla/5.0 (X11; Linux i686; rv:7.0.1) Gecko/20100101 Firefox/7.0.1',
                'X-Requested-With':'XMLHttpRequest',
                'Cookie':cookie,}

    get_url = taoci_url%(from_date,from_date,to_date,cat_id)

    http = httplib2.Http()
    headers, content = http.request(get_url,'GET',headers=headers)

    return headers,content



def liangzi_proxy(from_date=None,to_date=None,cat_id=None,cookie=None):

    headers = {
                'Accept':'*/*',
                'Accept-Charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                'Accept-Encoding':'gzip,deflate,sdch',
                'Accept-Language':'en-US,en;q=0.8',
                'Connection':'keep-alive',
                'User-Agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.75 Safari/535.7',
                'X-Requested-With':'XMLHttpRequest',
                'Cookie':cookie,}

    get_url = taoci_url%(from_date,from_date,to_date,cat_id)

    http = httplib2.Http()
    headers, content = http.request(get_url,'GET',headers=headers)

    return headers,content



@subway_proxy('bidword/queryScore4Words.htm',method='POST')
def bidword_queryScore4Words(token=None,campaignId=None,cookie=None,params={}):
    pass


