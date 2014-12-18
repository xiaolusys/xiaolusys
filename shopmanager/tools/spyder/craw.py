#-*- coding:utf8 -*-
import sys
import zlib
import re
import os
import cookielib
import urllib,urllib2
import httplib2
# 
headers = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Charset':'utf-8;q=0.7,*;q=0.3',
               'Accept-Encoding':'gzip,deflate',
               'Accept-Language':'en-US,en;q=0.8',
               'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0',
               'Referer':'http://www.zhe800.com/ju_tag/taofushi',
               'Connection':'keep-alive' }

ckjar = cookielib.MozillaCookieJar(os.path.join('/tmp/', 'cookies.txt'))
# uri = 'http://brand.zhe800.com/langshamuying'
uri = 'http://www.vip.com/detail-303792-40456880.html'
 
request = urllib2.Request(uri)
for k,v in headers.iteritems():
    print k,v
    request.add_header(k,v)
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(ckjar))
response = opener.open(request)
"""
['__contains__', '__delitem__', '__doc__', '__getitem__', '__init__', '__iter__', '__len__', '__module__', '__setitem__', '__str__', 
'addcontinue', 'addheader', 'dict', 'encodingheader', 'fp', 'get', 'getaddr', 'getaddrlist', 'getallmatchingheaders', 
'getdate', 'getdate_tz', 'getencoding', 'getfirstmatchingheader', 'getheader', 'getheaders', 'getmaintype', 'getparam', 
'getparamnames', 'getplist', 'getrawheader', 'getsubtype', 'gettype', 'has_key', 'headers', 'iscomment', 'isheader', 
'islast', 'items', 'keys', 'maintype', 'parseplist', 'parsetype', 'plist', 'plisttext', 'readheaders', 'rewindbody', 'seekable', 'setdefault', 
'startofbody', 'startofheaders', 'status', 'subtype', 'type', 'typeheader', 'unixfrom', 'values']"""
print dir(response),response.geturl()
print response.headers.getheaders('Content-Type')
html = response.read()
gzipped = response.headers.get('Content-Encoding')
if gzipped:
    html = zlib.decompress(html, 16+zlib.MAX_WBITS)
html = html.decode('utf-8')

# print u'你是中国人吗'



# headers = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#                'Accept-Charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
#                'Accept-Encoding':'gzip,deflate,sdch',
#                'Accept-Language':'en-US,en;q=0.8',
#                'User-Agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.75 Safari/535.7',
#                'Referer':'http://www.zhe800.com/ju_tag/taofushi\r\n',
#                #'Cookie':'session_id=1071618389.1417841920; utm_csr=direct; utm_ccn=notset_c0; utm_cmd=; utm_ctr=; utm_cct=; utm_etr=tao.others; firstTime=2014-12-06; lastTime=2014-12-09; frequency=1%2C1%2C0%2C1%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2',
#     }

#[truncated] Cookie: session_id=1071618389.1417841920; utm_csr=direct; utm_ccn=notset_c0; utm_cmd=; utm_ctr=; utm_cct=; utm_etr=tao.others; firstTime=2014-12-06; lastTime=2014-12-09; frequency=1%2C1%2C0%2C1%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2
# http = httplib2.Http()
# response,content = http.request(uri,'GET',headers=headers)
# 
# print response
print html
from BeautifulSoup import BeautifulSoup
soup = BeautifulSoup(html)
items =  soup.findAll(attrs={'class':'show_midpic '})[0].findAll('img')[0].attrMap.get('src','')
print 'items------------------------------',items
print dir(items[0])
print items[0].findParent().findAll('h4')[0]
for item in items:
    print item.findParent()
    print item.findParent().findAll('h4')[0].findAll('em')[0].text.replace('¥','')
#   print item.findAll('p')[0].text
    
    
    