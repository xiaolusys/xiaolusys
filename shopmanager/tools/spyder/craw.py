#-*- coding:utf8 -*-
import re
import urllib,urllib2
import httplib2
# 
# headers = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#                'Accept-Encoding':'gzip, deflate',
#                'Accept-Language':'en-US,en;q=0.8',
#                'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0'
#                }
# uri = 'http://brand.zhe800.com/langshamuying'
uri = 'http://shop.zhe800.com/products/ze141107015232000001?jump_source=1&qd_key=qyOwt6Jn#gonav'
#uri = 'http://youni.huyi.so/'
# request = urllib2.Request(uri,headers=headers)
# 
# response =  urllib2.urlopen(request, timeout=10)
# 
# print u'你是中国人吗'
# print response.read(),response.geturl(),response.info()

headers = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
               'Accept-Encoding':'gzip,deflate,sdch',
               'Accept-Language':'en-US,en;q=0.8',
               'User-Agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.75 Safari/535.7'
    }
http = httplib2.Http()
response,content = http.request(uri,'GET',headers=headers)

print response

from BeautifulSoup import BeautifulSoup
soup = BeautifulSoup(content)
items =  soup.findAll(attrs={'class' : 'nubB bm'})
for item in items[0:4]:
    print item
    print item.findAll('p')[0].text
    