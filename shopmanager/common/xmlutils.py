# -*- encoding:utf8 -*-

import xml2dict


def makeEasyTag(dom, tagname, value, type='text'):
    tag = dom.createElement(tagname)

    if value.find(']]>') > -1:
        type = 'text'
    if type == 'text':
        value = value.replace('&', '&amp;')
        value = value.replace('<', '&lt;')
        text = dom.createTextNode(value)
    elif type == 'cdata':
        text = dom.createCDATASection(value)

    tag.appendChild(text)

    return tag
