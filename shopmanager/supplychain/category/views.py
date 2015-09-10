# -*- encoding:utf-8 -*-
from rest_framework import generics
from rest_framework.renderers import JSONRenderer

from .models import (
    FirstCategory,
    SecondCategory,
    ThirdCategory,
    FourthCategory,
    FifthCategory,
    SixthCategory,
)

from .serializers import (
    FirstCategorySerializer,
    SecondCategorySerializer,
    ThirdCategorySerializer,
    FourthCategorySerializer,
    FifthCategorySerializer,
    SixthCategorySerializer,
)

# Create your views here.


class FirstCategoryList(generics.ListCreateAPIView):
    queryset = FirstCategory.objects.all()
    serializer_class = FirstCategorySerializer
    renderer_classes = (JSONRenderer,)


class SecondCategoryList(generics.ListCreateAPIView):
    queryset = SecondCategory.objects.all()
    filter_fields = ("parent",)
    serializer_class = SecondCategorySerializer
    renderer_classes = (JSONRenderer,)


class ThirdCategoryList(generics.ListCreateAPIView):
    queryset = ThirdCategory.objects.all()
    filter_fields = ("parent",)
    serializer_class = ThirdCategorySerializer
    renderer_classes = (JSONRenderer,)


class FourthCategoryList(generics.ListCreateAPIView):
    queryset = FourthCategory.objects.all()
    filter_fields = ("parent",)
    serializer_class = FourthCategorySerializer
    renderer_classes = (JSONRenderer,)


class FifthCategoryList(generics.ListCreateAPIView):
    queryset = FifthCategory.objects.all()
    filter_fields = ("parent",)
    serializer_class = FifthCategorySerializer
    renderer_classes = (JSONRenderer,)


class SixthCategoryList(generics.ListCreateAPIView):
    queryset = SixthCategory.objects.all()
    filter_fields = ("parent",)
    serializer_class = SixthCategorySerializer
    renderer_classes = (JSONRenderer,)



