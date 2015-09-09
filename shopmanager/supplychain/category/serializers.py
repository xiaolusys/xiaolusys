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


class SecondCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SecondCategory


class ThirdCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ThirdCategory


class FourthCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FourthCategory


class FifthCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FifthCategory


class SixthCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SixthCategory
        


    
