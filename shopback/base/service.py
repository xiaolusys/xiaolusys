# -*- coding:utf8 -*-

class LocalService():
    def __init__(self, t):
        pass

    @classmethod
    def createTrade(cls, user_id, tid, *args, **kwargs):
        raise Exception(u'方法未实现')

    @classmethod
    def createMergeTrade(cls, trade, *args, **kwargs):
        raise Exception(u'方法未实现')

    def payTrade(self, *args, **kwargs):
        raise Exception(u'方法未实现')

    def sendTrade(self, *args, **kwargs):
        raise Exception(u'方法未实现')

    def ShipTrade(self, *args, **kwargs):
        raise Exception(u'方法未实现')

    def finishTrade(self, *args, **kwargs):
        raise Exception(u'方法未实现')

    def closeTrade(self, *args, **kwargs):
        raise Exception(u'方法未实现')

    def memoTrade(self, *args, **kwargs):
        raise Exception(u'方法未实现')

    def changeTrade(self, *args, **kwargs):
        raise Exception(u'方法未实现')

    def changeTradeOrder(self, *args, **kwargs):
        raise Exception(u'方法未实现')

    def remindTrade(self, *args, **kwargs):
        raise Exception(u'方法未实现')


class LocalProductService():
    def __init__(self, t):
        pass

    @classmethod
    def createProduct(cls, user_id, tid, *args, **kwargs):
        raise Exception(u'方法未实现')
