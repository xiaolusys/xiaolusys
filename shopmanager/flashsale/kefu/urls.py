# coding:utf-8
from django.conf.urls import url
from flashsale.kefu import views



urlpatterns = [
    url(r'^add_record/$', views.AddRecordView.as_view(), name='searchProduct'),  # 搜索所有的商品 ajax

]
