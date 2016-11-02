__author__ = 'yann'
import sys
import datetime


def parse_datetime(target_time_str):
    return datetime.datetime.strptime(target_time_str, '%Y-%m-%d %H:%M:%S')


def parse_date(target_date_str):
    try:
        year, month, day = target_date_str.split('-')
        target_date = datetime.date(int(year), int(month), int(day))
        return target_date
    except:
        return datetime.date.today()

def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    # return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name

def get_supplier(sku_id):
    from shopback.items.models import ProductSku
    product_sku = ProductSku.objects.get(id=sku_id)
    product = product_sku.product

    from supplychain.supplier.models import SaleProduct
    try:
        sale_product = SaleProduct.objects.get(id=product.sale_product)
        supplier = sale_product.sale_supplier
        return supplier
    except SaleProduct.DoesNotExist:
        pass
    return None

def get_product(sku_id):
    from shopback.items.models import ProductSku
    try:
        product_sku = ProductSku.objects.get(id=sku_id)
        product = product_sku.product
        return product
    except ProductSku.DoesNotExist:
        pass
    return None

def get_unit_price(sku_id):
    from shopback.items.models import ProductSku
    product_sku = ProductSku.objects.get(id=sku_id)
    product = product_sku.product
    return product.cost

def copy_fields(to_obj, from_obj, fields):
    for field in fields:
        if hasattr(to_obj, field) and hasattr(from_obj, field):
            value = getattr(from_obj, field)
            setattr(to_obj, field, value)


def gen_purchase_detail_unikey(pa):
    sku_id = pa.sku_id
    sku_id = sku_id.strip()
    return "%s-%s" % (sku_id, pa.purchase_order_unikey)


def gen_purchase_order_unikey(pr):
    supplier = get_supplier(pr.sku_id)
    if not supplier:
        return 's0'
    
    from flashsale.dinghuo.models_purchase import PurchaseOrder
    cnt = PurchaseOrder.objects.filter(supplier_id=supplier.id).exclude(status=PurchaseOrder.OPEN).count()

    return '%s-%s' % (supplier.id, cnt+1)


def gen_purchase_arrangement_unikey(po_unikey, pr_unikey):
    return '%s-%s' % (po_unikey, pr_unikey)
