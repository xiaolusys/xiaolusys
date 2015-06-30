from rest_framework import viewsets

from shopback.items.models import Product
from flashsale.pay.models import SaleTrade

from .serializers import ProductSerializer, SaleTradeSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class SaleTradeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = SaleTrade.objects.all()
    serializer_class = SaleTradeSerializer# Create your views here.