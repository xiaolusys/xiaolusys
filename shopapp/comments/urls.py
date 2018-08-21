__author__ = 'meixqhi'
from django.conf.urls import include, url
from shopapp.comments.views import *

urlpatterns = [
    url('ignore/(?P<id>[^/]+)/$', comment_not_need_explain, name='comment_ignore'),
    url('explain/$', explain_for_comment, name='comment_explain'),
    url(r'^count/$', count),
    url(r'^replyer_detail/$', replyer_detail),
    url(r'^write_grade/$', write_grade),
    url(r'^replyer_grade/$', replyer_grade)
]
