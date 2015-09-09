import os
import re
import zlib
import cookielib
import urllib,urllib2
from BeautifulSoup import BeautifulSoup

ENCODING_RE               = re.compile('^.+charset=(?P<encoding>[\w]+)')
ckjar = cookielib.MozillaCookieJar(os.path.join('/tmp/', 'cookies.txt'))

def getBeaSoupByCrawUrl(fetch_url):
    headers = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Encoding':'gzip,deflate',
           'Accept-Language':'en-US,en;q=0.8',
           'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.120 Chrome/37.0.2062.120 Safari/537.36',
           'Referer':'https://www.taobao.com/',
           'Connection':'keep-alive'}
    
    request = urllib2.Request(fetch_url)
    for k,v in headers.iteritems():
        request.add_header(k,v)
        
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(ckjar))
    response = opener.open(request)
    
    if str(response.code).strip()  != '200':
        raise Exception(u'HTTP %s Error'%response.code )
    
    html = response.read()
    gzipped = response.headers.get('Content-Encoding')
    if gzipped:
        html = zlib.decompress(html, 16+zlib.MAX_WBITS)
        
    coding_str = response.headers.get('Content-Type')
    en_match = ENCODING_RE.match(coding_str)
    
    encoding = en_match and en_match.groupdict().get('encoding') 
    if not encoding:
        encoding = html.find('charset=utf-8') > 0 and 'utf-8' or 'gbk'

    return BeautifulSoup(html.decode(encoding)),response



        
        
        
        
        
    
        
    
    
    
    
    
