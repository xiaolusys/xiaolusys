# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url

from rest_framework import routers, viewsets
from .views import category

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'category', category.CategoryStatViewSet)

urlpatterns = [

]

urlpatterns += router.urls