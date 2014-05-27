from common.utils import update_model_fields


class BaseHandler(object):
    
    
    def handleable(self,*args,**kwargs):
        raise Exception('Not Implement.')
        
    def process(self,*args,**kwargs):
        raise Exception('Not Implement.')
    
    
class FinalHandler(object):
    
    def handleable(self,*args,**kwargs):
        return True
        
    def process(self,merge_trade,*args,**kwargs):
        
        if (merge_trade.reason_code and 
            not merge_trade.is_locked and 
            merge_trade.sys_status == MergeTrade.WAIT_PREPARE_SEND_STATUS):
            
            merge_trade.sys_status = MergeTrade.WAIT_AUDIT_STATUS
            update_model_fields(merge_trade,update_fields=['sys_status'])
        