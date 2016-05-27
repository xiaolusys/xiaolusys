
def gen_purchase_record_unikey(psi):
    return "%s-%s" % (psi.sale_order_id, psi.num_of_purchase_try)

def gen_purchase_order_unikey():
    pass
