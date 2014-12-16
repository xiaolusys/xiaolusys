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
    
#     template_name = "product_detail.html"

    
