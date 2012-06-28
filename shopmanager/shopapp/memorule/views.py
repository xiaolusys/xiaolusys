__author__ = 'meixqhi'
from djangorestframework.views import ModelView
from djangorestframework.response import ErrorResponse
from djangorestframework import status
from shopback.orders.models import Order,Trade,TradeExtraInfo
from shopback.items.models import Item
from shopback.users.models import User
from shopapp.memorule.models import TradeRule,ProductRuleField
from auth import apis
import logging

logger = logging.getLogger('app.memorule')



def to_memo_string(memo):
    s = [memo["post"]]
    s.append(memo["addr"])
    for product in memo["data"]:
        t = [product["pid"]]
        for k,v in product["property"].iteritems():
            t.append(k + ":" + v)
        s.append("|".join(t))
    return "\r\n".join(s)


def get_and_save_trade(seller_id,trade_id,session):
    try:
        trade = Trade.objects.get(pk=trade_id)
    except Trade.DoesNotExist:
        trade_dict = apis.taobao_trade_fullinfo_get(tid=trade_id,session=session)
        trade_dict = trade_dict['trade_fullinfo_get_response']['trade']
        trade = Trade.save_trade_through_dict(seller_id,trade_dict)

    return trade


def update_trade_memo(trade_id,trade_memo,session):
    try:
        trade_extra_info, created = TradeExtraInfo.objects.get_or_create(pk=trade_id)
        trade_extra_info.seller_memo = str(trade_memo)
        trade_info.save()
    except Exception,exc:
        return {"success": False, "message":"write memo to backend failed"}
    
    try:
        ms = to_memo_string(trade_memo)

        apis.taobao_trade_memo_update(tid=trade_id,memo=ms,session=session)
    except Exception,exc:
        return {"success": True, "message":"write memo to frontend failed"}
        
    return {"success": True}
    


class UpdateTradeMemoView(ModelView):

    def get(self, request, *args, **kwargs):
        content   = request.REQUEST
        params    = eval(content.get("params"))
        
        trade_id  = params.get('tid')
        user_id   = params.get('sid')

        try:
            profile = User.objects.get(visitor_id=user_id)
            session = profile.top_session
        except User.DoesNotExist:
            return {"success":False, "message":"no such seller id: "+user_id}
            #raise ErrorResponse("the seller id is not record!")

        return update_trade_memo(trade_id,params,session)
    

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
