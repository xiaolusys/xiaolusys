from django.conf.urls import url,include
import views
from rest_framework.urlpatterns import format_suffix_patterns
# urlpatterns = [
#     url(r'at_push/(?P<customer_id>\d+)/$',views.at_push,name='at_push')
# ]

urlpatterns = [
    url(r'at_push/(?P<customer_id>\d+)/$', views.LuntanPushViewSet.as_view('list')),
]

urlpatterns += format_suffix_patterns(urlpatterns)