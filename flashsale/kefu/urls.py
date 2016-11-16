# coding=utf-8
from django.conf.urls import url
from flashsale.kefu import views

urlpatterns = [
    url(r'^kefu_record/$', views.KefuRecordView.as_view(), name='kefu_record'),  # 查看客服记录
    url(r'^send_message/(?P<trade_id>\d+)/(?P<order_id>\d+)/$$', views.SendMessageView.as_view(), name='sendmessage'),
]
