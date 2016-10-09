from rest_framework import routers

import views

urlpatterns = []

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'STOthermal', views.STOThermalSet, 'STOthermal')

urlpatterns += router.urls



