#-*- coding:utf8 -*-
import datetime
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status

from flashsale.pay.models import SaleTrade,Customer

from . import permissions as perms
from . import serializers 

from flashsale.pay.models import SaleRefund,District,UserAddress,ShoppingCart

class SaleRefundViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = SaleRefund.objects.all()
    serializer_class = serializers.SaleRefundSerializer# Create your views here.
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
    def get_owner_queryset(self,request):
        customer = get_object_or_404(Customer,user=request.user)
        return self.queryset.filter(buyer_id=customer.id)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    
class UserAddressViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = UserAddress.objects.all()
    serializer_class = serializers.UserAddressSerializer# Create your views here.
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
    def get_owner_queryset(self,request):
        customer = get_object_or_404(Customer,user=request.user)
        return self.queryset.filter(cus_uid=customer.id)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)    
    
    
class DistrictViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = District.objects.all()
    serializer_class = serializers.DistrictSerializer# Create your views here.
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)    


class ShoppingCartViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = ShoppingCart.objects.all()
    serializer_class = serializers.ShoppingCartSerializer# Create your views here.
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
    def get_owner_queryset(self,request):
        customer = get_object_or_404(Customer,user=request.user)
        return self.queryset.filter(buyer_id=customer.id)
        
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)  
    
    
    