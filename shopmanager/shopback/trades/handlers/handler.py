
class BaseHandler(object):
    
    
    def handleable(self,*args,**kwargs):
        raise Exception('Not Implement.')
        
    def process(self,*args,**kwargs):
        raise Exception('Not Implement.')
        