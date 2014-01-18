#-*- coding:utf8 -*-
from shopback.users.models import User as Seller
from shopback import paramconfig as pcfg
        
def getUserBySellerId(seller_id):
    
    seller  = None
    try:
        seller  = Seller.objects.get(visitor_id=seller_id)
    except Seller.DoesNotExist:
        pass
    return seller
    
def getNormalSeller():
    return Seller.objects.filter(status=pcfg.USER_NORMAL)

def getDeleteSeller():
    return Seller.objects.filter(status=pcfg.USER_DELETE)
  
def getInactiveSeller():
    return Seller.objects.filter(status=pcfg.USER_INACTIVE)
  
def getFreezeSeller():
    return Seller.objects.filter(status=pcfg.USER_FREEZE)
  
def getSuperviseSeller():
    return Seller.objects.filter(status=pcfg.USER_SUPERVISE)