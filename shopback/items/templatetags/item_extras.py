# -*- coding:utf8 -*-
from django import template
from shopback.items.models import ProductSku

register = template.Library()


@register.filter(name='format_dt')
def format_dt(dt):
    return '%s%d,%s' % ('周', dt.date().isoweekday(), dt.strftime("%H时%M分"))


@register.filter(name='int_to_list')
def int_to_list(value):
    assert isinstance(value, int)
    return range(0, value)


@register.filter(name="get_sku_name")
def get_sku_name(sku, outer_id):
    outer_sku_id = sku.get('outer_id', '')
    try:
        psku = ProductSku.objects.get(outer_id=outer_sku_id, product__outer_id=outer_id)
    except:
        return u'商品规格未找到'
    else:
        return psku.name
