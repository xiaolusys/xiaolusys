__author__ = 'meixqhi'
import json
from djangorestframework.views import ModelView
from djangorestframework.response import ErrorResponse
from djangorestframework import status
from shopback.orders.models import Order,Trade
from shopback.items.models import Item
from shopback.users.models import User
from shopapp.memorule.models import TradeRule,ProductRuleField,RuleMemo
from auth import apis
import logging

logger = logging.getLogger('memorule.handler')



def to_memo_string(memo):
    s = [memo["post"]]
    s.append(memo["addr"])
    for product in memo["data"]:
        t = [product["pid"]]
        for k,v in product["property"].iteritems():
            t.append(k + ":" + v)
        s.append("|".join(t))
    return "\r\n".join(s)



def update_trade_memo(trade_id,trade_memo,user_id):
    
    try:
        rule_memo, created = RuleMemo.objects.get_or_create(pk=trade_id)
        rule_memo.rule_memo = json.dumps(trade_memo)
        rule_memo.is_used   = False
        rule_memo.save()
    except Exception,exc:
        return {"success": False, "message":"write memo to backend failed"}
    
    try:
        ms = to_memo_string(trade_memo)
        apis.taobao_trade_memo_update(tid=trade_id,memo=ms,tb_user_id=user_id)
    except Exception,exc:
        return {"success": True, "message":"write memo to taobao failed"}
        
    return {"success": True}
    


class UpdateTradeMemoView(ModelView):

    def get(self, request, *args, **kwargs):
        content   = request.REQUEST
        params    = eval(content.get("params"))
        
        trade_id  = params.get('tid')
        user_id   = params.get('sid')

        try:
            profile = User.objects.get(visitor_id=user_id)
        except User.DoesNotExist:
            return {"success":False, "message":"no such seller id: "+user_id}
            #raise ErrorResponse("the seller id is not record!")

        return update_trade_memo(trade_id,params,user_id=profile.visitor_id)
    

    post = get



class ProductRuleFieldsView(ModelView):

    def get(self, request, *args, **kwargs):
        content = request.REQUEST

        out_iids = content.get('out_iids')
        out_iid_list = out_iids.split(',')

        product_fields = []
        for out_iid in out_iid_list:

            trade_extras = ProductRuleField.objects.filter(outer_id=out_iid)
            trade_fields = [ extra.to_json() for extra in trade_extras]
            product_fields.append([out_iid,trade_fields])

        return product_fields

    post = get
