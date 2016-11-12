from django.conf.urls import *
from rest_framework import routers, viewsets

from .views import XiaoluAdministratorViewSet, GroupMamaAdministratorViewSet, LiangXiActivityViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'xiaoluadministrator', XiaoluAdministratorViewSet)
router.register(r'mamagroups', GroupMamaAdministratorViewSet)
router.register(r'liangxi', LiangXiActivityViewSet)

urlpatterns = router.urls