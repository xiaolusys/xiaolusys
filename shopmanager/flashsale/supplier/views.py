#-*- encoding:utf8 -*-
from .models import SaleSupplier,SaleCategory,SaleProduct
from .serializers import (
    SaleSupplierSerializer,
    PaginatedSaleSupplierSerializer,
    SaleCategorySerializer,
    SaleProductSerializer,
    PaginatedSaleProductSerializer
)
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer,TemplateHTMLRenderer
from shopback.base import log_action, ADDITION, CHANGE

class SaleSupplierList(generics.ListCreateAPIView):
    queryset = SaleSupplier.objects.all()
    serializer_class = SaleSupplierSerializer
    template_name = "supplier_list.html"
    

class SaleSupplierDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SaleSupplier.objects.all()
    serializer_class = SaleSupplierSerializer
    template_name = "supplier.html"

class SaleCategoryList(generics.ListCreateAPIView):
    queryset = SaleCategory.objects.all()
    serializer_class = SaleCategorySerializer

class SaleCategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SaleCategory.objects.all()
    serializer_class = SaleCategorySerializer
    

class SaleProductList(generics.ListCreateAPIView):
    queryset = SaleProduct.objects.all()
    serializer_class = SaleProductSerializer
    filter_fields = ("status","sale_supplier")
    #renderer_classes = (JSONRenderer,)
    #template_name = "product.html"

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.queryset)
        page = self.paginate_queryset(queryset)
        serializer = PaginatedSaleProductSerializer(page, context={'request': request})

        status =  request.QUERY_PARAMS.get("status")
        if not status:
            self.template_name = "product_list.html"
        elif SaleProduct.SELECTED in status:
            self.template_name = "product_screen.html"
        elif SaleProduct.PURCHASE in status:
            self.template_name = "product_finalize.html"
        else:
            self.template_name = "product_list.html"

        return Response(serializer.data)

class SaleProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SaleProduct.objects.all()
    serializer_class = SaleProductSerializer
    renderer_classes = (JSONRenderer,)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if not instance.contactor:
            instance.contactor = self.request.user
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        index_map = {SaleProduct.SELECTED:1,
                                        SaleProduct.PURCHASE:2,
                                        SaleProduct.PASSED:3}
            
        log_action(request.user.id,instance,CHANGE,(u'淘汰',u'初选入围',
                                                                                                u'洽谈通过',u'审核通过')[index_map.get(instance.status,0)])
        
        return Response(serializer.data)
    
#     template_name = "product_detail.html"

    
