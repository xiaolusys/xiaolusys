import json
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from shopback.items.models import Product,ProductSku

def productsku_quantity_view(request):
    
    #request.POST
    content     = request.REQUEST
    product_id  = content.get('product_id')
    sku_id      = content.get('sku_id')
    num         = int(content.get('num',''))
    
    sku = get_object_or_404(ProductSku,pk=sku_id,product__id=product_id)
    
    lock_success = Product.objects.isQuantityLockable(sku, num)
    
    resp  = {'success':lock_success}
    
    return HttpResponse(json.dumps(resp),content_type='application/json')
    