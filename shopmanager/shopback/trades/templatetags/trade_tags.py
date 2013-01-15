from django import template
from django.contrib.admin.templatetags.admin_list import result_headers,result_hidden_fields,results
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
    trade   = context.get('original',None)
    is_wait_audit   = True
    sys_status      = None
    can_split_trade = False
    can_trade_audit = False
    if trade :
        sys_status = trade.sys_status
        is_wait_audit = sys_status == pcfg.WAIT_AUDIT_STATUS
        can_split_trade = trade.has_merge or trade.has_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
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
        'show_split':can_split_trade and is_wait_audit and can_trade_audit,
        'show_invalid':is_wait_audit and can_trade_audit,
        'show_uninvalid':sys_status == pcfg.INVALID_STATUS and can_trade_audit,
        'show_unregular':sys_status == pcfg.REGULAR_REMAIN_STATUS and can_trade_audit,
        'show_save_and_regular':is_wait_audit and can_trade_audit,
        'show_save_and_aduit':False,
        'is_popup': is_popup,
        'show_save': True
    }
    
@register.inclusion_tag("admin/trades/change_list_results.html")
def trade_result_list(cl):
    """
    Displays the headers and data list together
    """
    headers = list(result_headers(cl))
    num_sorted_fields = 0
    for h in headers:
        if h['sortable'] and h['sorted']:
            num_sorted_fields += 1
    return {'cl': cl,
            'result_hidden_fields': list(result_hidden_fields(cl)),
            'result_headers': headers,
            'num_sorted_fields': num_sorted_fields,
            'results': list(results(cl))}    


@register.filter(name='prod_skus')  
def prod_skus(order):
    prods = ProductSku.objects.filter(prod_outer_id=order['outer_id'],status=pcfg.NORMAL)
    return prods
    
    
@register.filter(name='prod_name')  
def prod_name(order):
    if order['is_rule_match']:
        return order['title']
    try:
        prod = Product.objects.get(outer_id=order['outer_id'])
    except:
        p_name = order['title'] 
    else:
        p_name = prod.name or order['title']
    return p_name

@register.filter(name='sku_name')  
def sku_name(order):

    try:
        prod = ProductSku.objects.get(outer_id=order['outer_sku_id'],prod_outer_id=order['outer_id'])
    except:
        s_name = order['sku_properties_name']
    else:
        s_name = prod.properties_name or order['sku_properties_name']
    return s_name
