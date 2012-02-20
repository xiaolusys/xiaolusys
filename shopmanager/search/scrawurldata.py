import urllib
import urllib2
import urlparse
from lxml import etree
from StringIO import StringIO
import logging

logger = logging.getLogger('taobao.urlcraw')

baseurl = 'http://s.taobao.com/search'
itemhref_xpath = ['/html/body/div/div/div/div/div/form/ul/li/h3/a']
itemuser_xpath = ['/html/body/div/div/div/div/div/form/ul/li/p/a','/html/body/div/div/div/div/div/form/ul/li/ul/li/a']


def scraw_url(url):
    req =  urllib2.urlopen(url)
    html_text = req.read()
    parser = etree.HTMLParser()
    tree   = etree.parse(StringIO(html_text.decode('gbk')), parser)
    return tree


def parseElementAttr(tree):
    merge_list = []

    itemhref_list = []
    itemuser_list = []

    model = 'a'       #a,b instance taobao two styles page list

    for xpath in itemhref_xpath:
        itemhref_list = tree.xpath(xpath)
        if itemhref_list:
            break
        model = 'b'

    for xpath in itemuser_xpath:
        itemuser_list = tree.xpath(xpath)
        if itemuser_list:
            break
        model = 'b'

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
        itemdict['model'] = model

        itemdict['title'] = itemhref.attrib['title']
        itemdict['item_id'] = urlparse.parse_qs(o.query)['id'][0]

        o = urlparse.urlparse(itemuser.attrib['href'])
        try:
            itemdict['user_id'] = urlparse.parse_qs(o.query)['user_number_id'][0]
            itemdict['nick'] = itemuser.text
        except :
            logger.error('Get user_id error:%s'%itemuser_list[i].attrib,exc_info=True)

        merge_list.append(itemdict)

    return merge_list


def scrawTaoBaoPage(q,page_nums):

    merge_list = []
    for i in xrange(0,page_nums):
        params ={'q':q,'s':i*40}
        req_url = '%s?%s'%(baseurl,urllib.urlencode(params))
        tree = scraw_url(req_url)
        perpage_list = parseElementAttr(tree)
        merge_list.extend(perpage_list)

    return merge_list


def getTaoBaoPageRank(keyword,page_nums):

    keyword = keyword.encode('gbk')
    results = scrawTaoBaoPage(keyword,page_nums)

    for i in xrange(0,len(results)):
        item = results[i]
        if item['model'] == 'a':
            item['rank'] = i+3
        elif item['model'] == 'b':
            item['rank'] = i+4

    return results


def getCustomShopsPageRank(nicks,keywords,page_nums):

    search_results = {}
    for keyword in keywords:

        key_word = keyword.encode('gbk')
        results = scrawTaoBaoPage(key_word,page_nums)
        nick_results = {}
        for nick in nicks:

            nick = nick
            peruser_results = []

            for i in xrange(0,len(results)):
                item = results[i]

                if item['nick'] == nick:
                    if item['model'] == 'a':
                        item['rank'] = i+3
                    elif item['model'] == 'b':
                        item['rank'] = i+4
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














