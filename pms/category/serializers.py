from .models import (
    FirstCategory,
    SecondCategory,
    ThirdCategory,
    FourthCategory,
    FifthCategory,
    SixthCategory,
)

from rest_framework import serializers


class FirstCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FirstCategory
        exclude = ()


class SecondCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SecondCategory
        exclude = ()


class ThirdCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ThirdCategory
        exclude = ()


class FourthCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FourthCategory
        exclude = ()


class FifthCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FifthCategory
        exclude = ()


class SixthCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SixthCategory
        exclude = ()
        


    
