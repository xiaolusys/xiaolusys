from django.conf.urls import url,include
import views

urlpatterns = [
    url(r'at_push/(?P<customer_id>\d+)/$',views.at_push,name='at_push')
]

