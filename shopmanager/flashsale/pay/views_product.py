import json
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.forms import model_to_dict

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer,TemplateHTMLRenderer

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
    
    
    
class ProductDetailView(APIView):
    
    renderer_classes = (JSONRenderer,TemplateHTMLRenderer)
    template_name = "product/product_detail_img.html"
    #permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, pk, format=None):
        
        product = get_object_or_404(Product,id=pk)
        p_dict  = model_to_dict(product)
        p_dict['detail'] = product.detail
        p_dict['product_model'] = product.product_model
        p_dict['normal_skus'] = product.normal_skus
       
        return Response({'product':p_dict,'M_STATIC_URL':settings.M_STATIC_URL})
        