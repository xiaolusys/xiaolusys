from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from rest_framework import routers, viewsets

from .views import XiaoluAdministratorViewSet, GroupMamaAdministratorViewSet, LiangXiActivityViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'xiaoluadministrator', XiaoluAdministratorViewSet)
router.register(r'mamagroups', GroupMamaAdministratorViewSet)
router.register(r'liangxi', LiangXiActivityViewSet)

urlpatterns = router.urls