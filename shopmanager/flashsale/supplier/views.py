from models import SaleSupplier,SaleCategory,SaleProduct
from serializers import SaleSupplierSerializer,PaginatedSaleSupplierSerializer,SaleCategorySerializer,SaleProductSerializer,PaginatedSaleProductSerializer
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

class SaleSupplierList(generics.ListCreateAPIView):
    queryset = SaleSupplier.objects.all()
    serializer_class = SaleSupplierSerializer
    paginate_by = 10
    
    def get(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.queryset)
        serializer = PaginatedSaleSupplierSerializer(instance=page)
        
        return Response({'data': serializer.data,'page_number':page.number}, template_name='supplier.html')


class SaleSupplierDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SaleSupplier.objects.all()
    serializer_class = SaleSupplierSerializer
    

class SaleCategoryList(generics.ListCreateAPIView):
    queryset = SaleCategory.objects.all()
    serializer_class = SaleCategorySerializer

class SaleCategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SaleCategory.objects.all()
    serializer_class = SaleCategorySerializer
    

class SaleProductList(generics.ListCreateAPIView):
    queryset = SaleProduct.objects.all()
    serializer_class = SaleProductSerializer
    filter_fields = ("status",)
    #renderer_classes = (JSONRenderer,)
    #template_name = "product.html"

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.queryset)
        page = self.paginate_queryset(queryset)
        serializer = PaginatedSaleProductSerializer(page, context={'request': request})


        status =  request.QUERY_PARAMS.get("status")
        if not status:
            self.template_name = "product_list.html"
        elif "wait" in status:
            self.template_name = "product_screen.html"
        elif "selected" in status:
            self.template_name = "product_finalize.html"
        else:
            self.template_name = "product_list.html"

        return Response(serializer.data)

class SaleProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SaleProduct.objects.all()
    serializer_class = SaleProductSerializer
    renderer_classes = (JSONRenderer,)

    
