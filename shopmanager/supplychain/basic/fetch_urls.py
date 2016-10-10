# coding=utf-8
import os
import re
import urlparse
import zlib
import cookielib
import urllib2
from BeautifulSoup import BeautifulSoup

ENCODING_RE = re.compile('^.+charset=(?P<encoding>[\w]+)')
ckjar = cookielib.MozillaCookieJar(os.path.join('/tmp/', 'cookies.txt'))


def getBeaSoupByCrawUrl(fetch_url):
    headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Encoding': 'gzip, deflate, sdch',
               'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
               'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/44.0.2403.89 Chrome/44.0.2403.89 Safari/537.36',
               # 'Referer':'http://www.baidu.com',
               'Connection': 'keep-alive'}

    request = urllib2.Request(fetch_url)
    for k, v in headers.iteritems():
        request.add_header(k, v)

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(ckjar))
    response = opener.open(request)

    if str(response.code).strip() != '200':
        raise Exception(u'HTTP %s Error' % response.code)

    html = response.read()
    gzipped = response.headers.get('Content-Encoding')
    if gzipped:
        html = zlib.decompress(html, 16 + zlib.MAX_WBITS)

    coding_str = response.headers.get('Content-Type')
    en_match = ENCODING_RE.match(coding_str)

    encoding = en_match and en_match.groupdict().get('encoding')
    if not encoding:
        encoding = html.find('charset=utf-8') > 0 and 'utf-8' or 'gbk'

    return BeautifulSoup(html.decode(encoding)), response


def getItemPrice(soup):
    return 0


def get_img_src(img):
    attr_map = dict(img.attrs)
    img_src = attr_map and attr_map.get('src') or attr_map.get('data-src')
    if img_src and img_src.split('?')[0].endswith('.jpg'):
        return img_src
    return ''


def get_link_img_src(link):
    for img in link.findAll('img'):
        return get_img_src(img)
    return ''


def getItemPic(fetch_url, soup):
    pic_path_pattern = re.compile(r'(.+\.jpg)_.+')
    container = soup.findAll(attrs={'class': re.compile(
        '^(deteilpic|zoomPad|SPSX_bian3|goods-detail-pic|container|florid-goods-page-container|m-item-grid|cloud-zoom)')
                                    })

    for c in container:
        for img in c.findAll('img'):
            img_src = get_img_src(img)
            if img_src:
                image_url_components = urlparse.urlparse(img_src)
                if not image_url_components.netloc:
                    fetch_url_components = urlparse.urlparse(fetch_url)
                    return '%s://%s%s' % (fetch_url_components.scheme,
                                          fetch_url_components.netloc,
                                          image_url_components.path)
                return img_src

    alinks = soup.findAll('a')
    for a in alinks:
        img_src = get_link_img_src(a)
        m = pic_path_pattern.match(img_src)
        if m:
            return m.group(1)
        if img_src:
            image_url_components = urlparse.urlparse(img_src)
            if not image_url_components.netloc:
                fetch_url_components = urlparse.urlparse(fetch_url)
                return '%s://%s%s' % (fetch_url_components.scheme,
                                      fetch_url_components.netloc,
                                      image_url_components.path)
            return img_src
    return ''


def getItemTitle(soup):
    try:
        return soup.findAll('title')[0].text.strip()
    except:
        return ''


def supplier_sku(fetch_url, soup):
    fetch_url_components = urlparse.urlparse(fetch_url)
    host_name = fetch_url_components.netloc

    def _is_1688():
        return '1688' in host_name.split('.')

    def _is_tmall():
        return 'tmall' in host_name.split('.')

    def _is_gongxiao():
        return 'gongxiao' in host_name.split('.')

    def _get_1688():
        sku_tag = None
        for tag in soup.findAll('td', attrs={'class': re.compile('de-feature')}):
            if tag.text == u'货号':
                sku_tag = tag.findNextSibling('td', attrs={'class': re.compile('de-value')})
        if sku_tag:
            return sku_tag.text.strip()

    if _is_1688():
        return _get_1688()
    return ''
