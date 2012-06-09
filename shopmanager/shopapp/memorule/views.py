__author__ = 'meixqhi'
import json
from django.http import HttpResponse
from djangorestframework.views import ModelView
from djangorestframework.response import ErrorResponse
from djangorestframework import status
from shopback.orders.models import Order,Trade
from shopback.items.models import Item
from shopback.users.models import User
from shopapp.memorule.models import TradeRule
from auth import apis
import logging

logger = logging.getLogger('app.memorule')


def is_over_lap(set_a,set_b):
    len_a = len(set_a)
    len_b = len(set_b)
    set_a.union(set_b)
    if len(set_a)<len_a+len_b:
        return True
    return False



def gen_memo_by_params(params,trade):

    trade_rules = TradeRule.objects.filter(status='US').order_by('-priority')
    rule_list = []
    rule_ids  = set([])
    orders = trade.trade_orders.all()
    for rule in trade_rules:
        try:
            memo_str = None
            opposite_ids = rule.opposite_ids
            if not opposite_ids:
                opposite_ids = set([])
            else :
                opposite_ids = set(json.loads(opposite_ids))

            over_lap = is_over_lap(rule_ids,opposite_ids)

            if rule.scope == 'trade':
                if not over_lap and eval(rule.formula):
                    memo_str = eval(rule.match_tpl_memo)
                    rule_ids.add(rule.id)
                else:
                    memo_str = eval(rule.unmatch_tpl_memo)

            else:
                for order in orders:
                    try:
                        item = Item.objects.get(num_iid=order.num_iid)
                    except Item.DoesNotExist:
                        item = None

                    if not over_lap and eval(rule.formula):
                        memo_str = eval(rule.match_tpl_memo)
                        rule_ids.add(rule.id)
                        break

                if memo_str == None :
                    memo_str = eval(rule.unmatch_tpl_memo)
            if memo_str:
                rule_list.append(memo_str)

        except Exception,exc:
            logger.error('%s'%exc,exc_info=True)

    return '&'.join(rule_list)



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
        apis.taobao_trade_memo_update(tid=trade_id,memo=trade_memo,session=session)
    except Exception,exc:
        raise ErrorResponse('%s'%exc)

    try:
        trade = Trade.objects.get(pk=trade_id)
        trade.seller_memo = trade_memo
        trade.save()
    except Trade.DoesNotExist:
        pass



class UpdateTradeMemoView(ModelView):

    def get(self, request, *args, **kwargs):
        content  = request.REQUEST

        trade_id    = content.get('tid')
        seller_id   = content.get('seller_id')

        try:
            profile = User.objects.get(visitor_id=seller_id)
            session = profile.top_session
        except User.DoesNotExist:
            raise ErrorResponse("the seller id is not record!")


        trade = get_and_save_trade(seller_id,trade_id,session)
        trade_memo = gen_memo_by_params(content,trade)

        update_trade_memo(trade_id,trade_memo,session)

        return {'trade_memo':trade_memo}

    post = get