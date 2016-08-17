
def get_sale_order_mama_id(sale_order):
    sale_trade = sale_order.sale_trade
    extra = sale_trade.extras_info
    mama_id  = 0   # 推荐人妈妈id
    if 'mm_linkid' in extra:
        mama_id = int(extra['mm_linkid'] or '0')
    return mama_id

