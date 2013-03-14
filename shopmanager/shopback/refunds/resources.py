__author__ = 'meixqhi'
from djangorestframework.resources import ModelResource


class RefundProductResource(ModelResource):
    """ docstring for RefundProductResource """

    fields = ('refund_id','id','buyer_nick','buyer_mobile','buyer_phone','trade_id','out_sid','sid','mobile','phone'
              ,'company','title','property','num','can_reuse','is_finish','created','modified','memo','status')
    exclude = ('url',) 
    
    
class RefundResource(ModelResource):
    """ docstring for RefundResource """

    fields = ('refund_id','tid','title','num_iid','buyer_nick','seller_nick','mobile','phone','total_fee','refund_fee','property'
              ,'payment','oid','company_name','sid','reason','desc','has_good_return','created','modified','good_status','status')
    exclude = ('url',) 
    