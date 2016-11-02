#-*- coding:utf8 -*-
from django.conf import settings
from django.core import exceptions
from shopback import paramconfig as pcfg
from .handler import (BaseHandler,
                      InitHandler,
                      ConfirmHandler,
                      FinalHandler,
                      StockOutHandler,
                      DefectHandler,
                      RuleMatchHandler)
from .split    import SplitHandler
from .memo     import MemoHandler
from .merge    import MergeHandler
from .refund   import RefundHandler
from .logistic import LogisticsHandler
from .intercept import InterceptHandler
from .regular import RegularSaleHandler
from .flashsale import FlashSaleHandler

import logging
logger = logging.getLogger('celery.handler')

class NotBaseHandlerError(Exception):
    pass

class AlreadyRegistered(Exception):
    pass

class TradeHandler(object):
    
    def __init__(self, name='handlers', app_name='trades'):
        
        self._handlers = [] #collect all need effect handlers
        
        
    def register(self,handler_class):
        
        if not handler_class or not issubclass(handler_class,BaseHandler):
            raise NotBaseHandlerError('Need Trade BaseHandler Subclass.')
        
        handler = handler_class()
        
        for registed_handler in self._handlers:
            if type(handler) == type(registed_handler):
                raise AlreadyRegistered(u'%s is already regiest.'%unicode(type(handler)))
            
        self._handlers.append(handler)
        
    def proccess(self,merge_trade,*args,**kwargs):
        
        try:
            for registed_handler in self._handlers:
                if registed_handler.handleable(merge_trade,*args,**kwargs):
                    registed_handler.process(merge_trade,*args,**kwargs)
        except Exception,exc:
            merge_trade.append_reason_code(pcfg.SYSTEM_ERROR_CODE)
            
            logger.error(u'订单处理错误:%s'%exc.message,exc_info=True)
            
        
        
def getTradeHandler(config_handlers_path=[]):

    from importlib import import_module
    
    trade_handler =  TradeHandler()
    config_handlers_path = config_handlers_path or getattr(settings,'TRADE_HANDLERS_PATH',[])
    for handler_path in config_handlers_path:
        try:
            hl_module, hl_classname = handler_path.rsplit('.', 1)
        except ValueError:
            raise exceptions.ImproperlyConfigured('%s isn\'t a middleware module' % handler_path)
        
        try:
            mod = import_module(hl_module)
        except ImportError, e:
            raise exceptions.ImproperlyConfigured('Error importing middleware %s: "%s"' % (hl_module, e))
        
        try:
            hl_class = getattr(mod, hl_classname)
        except AttributeError:
            raise exceptions.ImproperlyConfigured('Middleware module "%s" does not define a "%s" class' 
                                                  % (hl_module, hl_classname))
        
        trade_handler.register(hl_class)
        
    return trade_handler

trade_handler = getTradeHandler()
    