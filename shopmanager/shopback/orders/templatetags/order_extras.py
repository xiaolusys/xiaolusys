from django import template

register = template.Library()



@register.filter(name='split_axis')
def splitaxis(value):
    assert isinstance(value,(list,tuple))
    item_dict = {}
    for item in value:
        if item['yAxis'] == 0:
            if not item_dict.has_key(item['name']):
                item_dict[item['name']] = {}
            item_dict[item['name']]['num_data'] = item['data']
        else:
            if not item_dict.has_key(item['name']):
                item_dict[item['name']] = {}
            item_dict[item['name']]['sales_data'] = item['data']

    return item_dict
 
 
 
@register.filter(name='array_sum')  
def arraysum(value):   
    assert isinstance(value,(list,tuple))
    sum = 0
    for v in value:
        if v:
            sum += v
    return sum    

         