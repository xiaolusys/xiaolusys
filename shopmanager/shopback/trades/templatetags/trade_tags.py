from django import template
from shopback import paramconfig as pcfg
from shopback.trades.models import MergeTrade
from shopback.items.models import Product,ProductSku

register = template.Library()

@register.inclusion_tag('admin/trades/submit_line.html', takes_context=True)
def trade_submit_row(context):
    """
    Displays the row of buttons for delete and save.
    """
    opts = context['opts']
    change = context['change']
    is_popup = context['is_popup']
    save_as = context['save_as']
    trade   = context['original']
    sys_status = trade.sys_status
    is_wait_audit = sys_status == pcfg.WAIT_AUDIT_STATUS
    can_trade_audit = context['perms'].user.has_perm('trades.can_trade_aduit')
    return {
        'onclick_attrib': (opts.get_ordered_objects() and change
                            and 'onclick="submitOrderForm();"' or ''),
        'show_delete_link': (not is_popup and context['has_delete_permission']
                              and (change or context['show_delete'])),
        'show_save_as_new': not is_popup and change and save_as,
        'show_save_and_add_another': context['has_add_permission'] and
                            not is_popup and (not save_as or context['add']),
        'show_save_and_continue': context['has_change_permission'],
        'show_close':True ,
        'show_split':trade.has_merge and is_wait_audit and can_trade_audit,
        'show_invalid':is_wait_audit and can_trade_audit,
        'show_uninvalid':sys_status == pcfg.INVALID_STATUS and can_trade_audit,
        'show_unregular':sys_status == pcfg.REGULAR_REMAIN_STATUS and can_trade_audit,
        'show_save_and_regular':is_wait_audit and can_trade_audit,
        'show_save_and_aduit':is_wait_audit and can_trade_audit,
        'is_popup': is_popup,
        'show_save': True
    }

@register.filter(name='prod_skus')  
def prod_skus(order):
    prods = ProductSku.objects.filter(prod_outer_id=order['outer_id'])
    return prods
    