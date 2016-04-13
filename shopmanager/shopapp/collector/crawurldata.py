import time
import datetime
import urllib
import urllib2
import httplib2
import urlparse
from lxml import etree
from StringIO import StringIO
from common.utils import format_datetime

import logging

logger = logging.getLogger('django.request')

baseurl = 'http://s.taobao.com/search'
trade_url = 'http://tbskip.taobao.com/json/show_buyer_list.htm'  # page_size=15&item_id=7402446227&seller_num_id=129712885&bidPage=1&ends=1331277827000&starts=1330673027000

head_xpath = '/html/body/div/div/div/div/div/form/div/ul/li'
item_xpath = '/html/body/div/div/div/div/div/form/ul/li'

trade_xpath = '/html/body/table/tr'


def craw_url(url):
    headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
               'Accept-Encoding': 'gzip,deflate,sdch',
               'Accept-Language': 'en-US,en;q=0.8',
               'User-Agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.75 Safari/535.7'
               }
    http = httplib2.Http()
    response, content = http.request(url, 'GET', headers=headers)
    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(content.decode('gbk')), parser)
    return tree


def parseRankElementAttr(tree, tree_xpath):
    merge_list = []
    elements = tree.xpath(tree_xpath)

    for e in elements:
        itemdict = {}
        prod = e.xpath('h3/a')
        user = e.xpath('p/a') or e.xpath('ul/li/a')
        pic = e.xpath('div/a/span/img')

        itemdict['title'] = prod[0].attrib['title']
        o = urlparse.urlparse(prod[0].attrib['href'])

        params = urlparse.parse_qs(o.query)
        if not params.has_key('id') and params.has_key('url'):
            o = urlparse.urlparse(params['url'][0])
            itemdict['item_id'] = urlparse.parse_qs(o.query)['id'][0]
        else:
            itemdict['item_id'] = params['id'][0]

        o = urlparse.urlparse(user[0].attrib['href'])

        itemdict['user_id'] = urlparse.parse_qs(o.query)['user_number_id'][0]
        itemdict['nick'] = user[0].text

        itemdict['pic_url'] = pic[0].attrib.get('src', None) or pic[0].attrib.get('data-ks-lazyload', None)
        merge_list.append(itemdict)

    return merge_list


def parseTradeElementAttr(tree, trade_xpath):
    trade_elements = tree.xpath(trade_xpath)

    if not trade_elements:
        return None
    trade_elements = trade_elements[1:]
    trades = []

    for trade_tree in trade_elements:
        trade = {}
        tds = trade_tree.xpath('td')
        td1 = tds[1].find('a')
        o = urlparse.urlparse(td1.attrib['href'])
        trade['title'] = td1.text
        trade['trade_id'] = urlparse.parse_qs(o.query)['trade_id'][0]

        trade['price'] = tds[2].find('em').text
        trade['num'] = tds[3].text
        trade['trade_at'] = tds[4].text
        trade['state'] = tds[5].text

        trades.append(trade)

    return trades


def crawTaoBaoPage(q, page_nums):
    merge_list = []
    for i in xrange(0, page_nums):
        params = {'q': q, 's': i * 40}
        req_url = '%s?%s' % (baseurl, urllib.urlencode(params))
        tree = craw_url(req_url)
        if i == 0:
            head_list = parseRankElementAttr(tree, head_xpath)
            if head_list:
                merge_list.extend(head_list)

        perpage_list = parseRankElementAttr(tree, item_xpath)
        if not perpage_list:
            return merge_list
        merge_list.extend(perpage_list)

    return merge_list


def crawTaoBaoTradePage(item_id, seller_num_id, start_dt, end_dt):
    merge_list = []

    ends = time.mktime(time.strptime(end_dt, "%Y-%m-%d %H:%M:%S")) * 1000
    starts = time.mktime(time.strptime(start_dt, "%Y-%m-%d %H:%M:%S")) * 1000

    page_no = 1
    has_next = True
    retry = 0
    while True:
        params = {'page_size': 15, 'item_id': item_id, 'seller_num_id': seller_num_id
            , 'ends': int(ends), 'starts': int(starts), 'bidPage': page_no}
        req_url = '%s?%s' % (trade_url, urllib.urlencode(params))
        tree = craw_url(req_url)
        trades = parseTradeElementAttr(tree, trade_xpath)
        if not trades:
            if retry == 3:
                break
            time.sleep(5)
            retry += 1
            continue

        retry = 0
        for trade in trades:
            if trade['trade_at'] < start_dt:
                has_next = False
                break
            if trade['trade_at'] < end_dt and trade['trade_at'] > start_dt:
                merge_list.append(trade)

        if not has_next:
            break

        page_no += 1
    return merge_list


def getTaoBaoPageRank(keyword, page_nums):
    keyword = keyword.encode('gbk')
    results = crawTaoBaoPage(keyword, page_nums)

    for i in xrange(0, len(results)):
        item = results[i]
        item['rank'] = i + 1

    return results


def getCustomShopsPageRank(nicks, keywords, page_nums):
    search_results = {}
    for keyword in keywords:

        key_word = keyword.encode('gbk')
        results = crawTaoBaoPage(key_word, page_nums)
        nick_results = {}
        for nick in nicks:

            nick = nick
            peruser_results = []

            for i in xrange(0, len(results)):
                item = results[i]

                if item['nick'] == nick:
                    item['rank'] = i + 1
                    peruser_results.append(item)

            nick_results[nick] = peruser_results

        search_results[keyword] = nick_results

    return search_results
