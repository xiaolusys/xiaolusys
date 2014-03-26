
class TradeHandler(object):
    
    merge_trade     = None
    first_pay_load  = False
    
    def __init__(self,trade,first_pay_load=True):
        self.merge_trade = trade
        self.first_pay_load = first_pay_load
    
    def handleable(self):
        raise Exception('Not Implement.')
        
    def process(self,*args,**kwargs):
        raise Exception('Not Implement.')
        