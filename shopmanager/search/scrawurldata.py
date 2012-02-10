import urllib
import urllib2
import urlparse
from lxml import etree
from StringIO import StringIO

nicks = ['\xe4\xbc\x98\xe5\xb0\xbc\xe4\xb8\x96\xe7\x95\x8c\xe6\x97\x97\xe8\x88\xb0\xe5\xba\x97'
         ,'\xe4\xbc\x98\xe5\xb0\xbc\xe5\xb0\x8f\xe5\xb0\x8f\xe4\xb8\x96\xe7\x95\x8c']
keywords = ['\xe7\x9d\xa1\xe8\xa2\x8b \xe5\x84\xbf\xe7\xab\xa5 \xe9\x98\xb2\xe8\xb8\xa2\xe8\xa2\xab',]

baseurl = 'http://s.taobao.com/search'
itemhref_xpath = '/html/body/div/div/div/div/div/form/ul/li/h3/a'
itemuser_xpath = '/html/body/div/div/div/div/div/form/ul/li/p/a'


def scraw_url(url):
    req =  urllib2.urlopen(url)
    html_text = req.read()
    parser = etree.HTMLParser()
    tree   = etree.parse(StringIO(html_text.decode('gbk')), parser)
    return tree


def parseElementAttr(tree):
    merge_list = []
    itemhref_list = tree.xpath(itemhref_xpath)
    itemuser_list = tree.xpath(itemuser_xpath)

    if len(itemuser_list)>len(itemhref_list):
        for user in itemuser_list:
            if user.attrib.has_key('title'):
                itemuser_list.remove(user)


    for i in xrange(0,len(itemhref_list)):
        itemhref = itemhref_list[i]
        itemuser = itemuser_list[i]

        itemdict = {}

        o = urlparse.urlparse(itemhref.attrib['href'])
        itemdict['title'] = itemhref.attrib['title']
        itemdict['item_id'] = urlparse.parse_qs(o.query)['id'][0]

        o = urlparse.urlparse(itemuser.attrib['href'])
        try:
            itemdict['user_id'] = urlparse.parse_qs(o.query)['user_number_id'][0]
            itemdict['nick'] = itemuser.text
        except :
            print 'get user_id error:',itemuser_list[i].attrib

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


def getTaoBaoPageRank(nick,keyword,page_nums):

    nick = nick.decode('utf8')
    keyword = keywords.decode('utf8').encode('gbk')
    results = scrawTaoBaoPage(keyword,page_nums)
    search_results = []

    for i in xrange(0,len(results)):
        item = results[i]
        if item['nick'] == nick:
            item['rank'] = i+i
            search_results.append(item)

    return search_results


def getCustomShopsPageRank(nicks,keywords,page_nums):

    search_results = {}
    for keyword in keywords:

        key_word = keyword.decode('utf8').encode('gbk')
        results = scrawTaoBaoPage(key_word,page_nums)

        nick_results = {}
        for nick in nicks:

            nick = nick.decode('utf8')
            peruser_results = []

            for i in xrange(0,len(results)):
                item = results[i]
                if item['nick'] == nick:
                    item['rank'] = i+1
                    peruser_results.append(item)

            nick_results[nick] = peruser_results

        search_results[keyword] = nick_results

    return search_results


if __name__ == '__main__':

    results = getCustomShopsPageRank(nicks,keywords,5)

    for keyword,nicks_result in  results.iteritems():

        for nick,values in nicks_result.iteritems():

            print keyword,'---------',nick

            for value in values:
                print value['title'],'=======',value['rank']














