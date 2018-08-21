# coding: utf-8 
from django.conf.urls import url
from django.views.generic import TemplateView

from core.weixin.decorators import weixin_authlogin_required
from . import views
from . import views_dress

urlpatterns = [
    # url(r'^examination_user/$','examination_user'),
    # url(r'^start_exam/$','start_exam'),
    url(r'^$', views.index, name='index'),
    url(r'^mmexam/(?P<question_id>\d+)/$', views.exam, name='exam'),
    # url(r'^correct_problem_count/$','correct_problem_count'),

    url(r'^dress/$', views_dress.DressView.as_view(), name="dress_home"),
    url(r'^dress/age/$', views_dress.DressAgeView.as_view(), name="dress_age"),
    url(r'^dress/result/$', views_dress.DressResultView.as_view(), name="dress_result"),
    url(r'^dress/share/(?P<dress_id>\d+)/$', views_dress.DressShareView.as_view(),
       name="dress_share"),
    url(r'^dress/(?P<active_id>\d+)/$',
       weixin_authlogin_required(redirecto='/pages/denglu.html')(
           views_dress.DressQuestionView.as_view())
       , name="dress_question")
]
