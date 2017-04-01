from django.conf.urls import include, url
from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    FirstCategoryList,
    SecondCategoryList,
    ThirdCategoryList,
    FourthCategoryList,
    FifthCategoryList,
    SixthCategoryList,
)

urlpatterns = [
    url(r'^1st/$', FirstCategoryList.as_view()),
    url(r'^2nd/$', SecondCategoryList.as_view()),
    url(r'^3rd/$', ThirdCategoryList.as_view()),
    url(r'^4th/$', FourthCategoryList.as_view()),
    url(r'^5th/$', FifthCategoryList.as_view()),
    url(r'^6th/$', SixthCategoryList.as_view()),
]

urlpattens = format_suffix_patterns(urlpatterns)
