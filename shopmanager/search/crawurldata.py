import time
import datetime
import urllib
import urllib2
import urlparse
from lxml import etree
from StringIO import StringIO
from auth.utils import format_datetime

import logging

logger = logging.getLogger('taobao.urlcraw')

baseurl = 'http://s.taobao.com/search'
trade_url = 'http://tbskip.taobao.com/json/show_buyer_list.htm' #page_size=15&item_id=7402446227&seller_num_id=129712885&bidPage=1&ends=1331277827000&starts=1330673027000

head_href_xpath = ['/html/body/div/div/div/div/div/form/div/ul/li/h3/a','/html/body/div/div/div/div/div/form/div/ul/li/h3/a']
head_user_xpath = ['/html/body/div/div/div/div/div/form/div/ul/li/p/a','/html/body/div/div/div/div/div/form/div/ul/li/ul/li/a']
item_href_xpath = ['/html/body/div/div/div/div/div/form/ul/li/h3/a']
item_user_xpath = ['/html/body/div/div/div/div/div/form/ul/li/p/a','/html/body/div/div/div/div/div/form/ul/li/ul/li/a']

trade_xpath = '/html/body/table/tr'

def craw_url(url):
    req =  urllib2.urlopen(url)
    html_text = req.read()
    parser = etree.HTMLParser()
    tree   = etree.parse(StringIO(html_text.decode('gbk')), parser)
    return tree



def parseElementAttr(tree,itemhref_xpath,itemuser_xpath):
    merge_list = []

    itemhref_list = []
    itemuser_list = []

    for xpath in itemhref_xpath:
        itemhref_list = tree.xpath(xpath)
        if itemhref_list:
            break

    for xpath in itemuser_xpath:
        itemuser_list = tree.xpath(xpath)
        if itemuser_list:
            break

    if len(itemuser_list)>len(itemhref_list):
        for user in itemuser_list:
            if user.attrib.has_key('title'):
                itemuser_list.remove(user)

    if len(itemhref_list) != len(itemuser_list):
        itemhref_list = itemuser_list = []
        logger.warn('Taobao page data is not parse right!itemhref len is %s and itemuser_list len is %s'
                    %(len(itemhref_list),len(itemuser_list)))

    for i in xrange(0,len(itemhref_list)):
        itemhref = itemhref_list[i]
        itemuser = itemuser_list[i]

        itemdict = {}

        o = urlparse.urlparse(itemhref.attrib['href'])

        itemdict['title'] = itemhref.attrib['title']

        params = urlparse.parse_qs(o.query)
        if not params.has_key('id') and params.has_key('url'):
            o = urlparse.urlparse(params['url'][0])
            itemdict['item_id'] = urlparse.parse_qs(o.query)['id'][0]
        else:
            itemdict['item_id'] = params['id'][0]

        o = urlparse.urlparse(itemuser.attrib['href'])
        try:
            itemdict['user_id'] = urlparse.parse_qs(o.query)['user_number_id'][0]
            itemdict['nick'] = itemuser.text
        except :
            logger.error('Get user_id error:%s'%itemuser_list[i].attrib,exc_info=True)

        merge_list.append(itemdict)

    return merge_list



def parseTradeElementAttr(tree,trade_xpath):

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
        trade['num']   = tds[3].text
        trade['trade_at'] = tds[4].text
        trade['state'] = tds[5].text

        trades.append(trade)

    return trades



def crawTaoBaoPage(q,page_nums):

    merge_list = []
    for i in xrange(0,page_nums):
        params ={'q':q,'s':i*40}
        req_url = '%s?%s'%(baseurl,urllib.urlencode(params))
        tree = craw_url(req_url)
        if i == 0:
            head_list = parseElementAttr(tree,head_href_xpath,head_user_xpath)
            merge_list.extend(head_list)

        perpage_list = parseElementAttr(tree,item_href_xpath,item_user_xpath)
        merge_list.extend(perpage_list)

    return merge_list



def crawTaoBaoTradePage(item_id,seller_num_id,start_dt,end_dt):
    merge_list = []

    ends = time.mktime(time.strptime(end_dt, "%Y-%m-%d %H:%M:%S"))*1000
    starts = time.mktime(time.strptime(start_dt, "%Y-%m-%d %H:%M:%S"))*1000

    page_no = 1
    has_next = True
    retry = 0
    while True:
        params ={'page_size':15,'item_id':item_id,'seller_num_id':seller_num_id
                 ,'ends':int(ends),'starts':int(starts),'bidPage':page_no}
        req_url = '%s?%s'%(trade_url,urllib.urlencode(params))
        tree = craw_url(req_url)
        trades = parseTradeElementAttr(tree,trade_xpath)
        if not trades:
            if retry == 4:
                break
            time.sleep(5)
            retry += 1
            continue

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



def getTaoBaoPageRank(keyword,page_nums):

    keyword = keyword.encode('gbk')
    results = crawTaoBaoPage(keyword,page_nums)

    for i in xrange(0,len(results)):
        item = results[i]
        item['rank'] = i+1

    return results



def getCustomShopsPageRank(nicks,keywords,page_nums):

    search_results = {}
    for keyword in keywords:

        key_word = keyword.encode('gbk')
        results = crawTaoBaoPage(key_word,page_nums)
        nick_results = {}
        for nick in nicks:

            nick = nick
            peruser_results = []

            for i in xrange(0,len(results)):
                item = results[i]

                if item['nick'] == nick:
                    item['rank'] = i+1
                    peruser_results.append(item)

            nick_results[nick] = peruser_results

        search_results[keyword] = nick_results

    return search_results



#if __name__ == '__main__':

#    results = getCustomShopsPageRank(nicks,keywords,5)
#
#    for keyword,nicks_result in  results.iteritems():
#
#        for nick,values in nicks_result.iteritems():
#
#            print keyword,'---------',nick
#
#            for value in values:
#                print value['title'],'=======',value['rank']














