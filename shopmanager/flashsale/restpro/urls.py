# coding: utf-8

from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from django.views.decorators.cache import cache_page
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework import routers

from flashsale.restpro.v2 import views_lesson
lesson_router = routers.DefaultRouter(trailing_slash=False)
lesson_router.register(r'lessontopic', views_lesson.LessonTopicViewSet)
lesson_router.register(r'lesson', views_lesson.LessonViewSet)
lesson_router.register(r'instructor', views_lesson.InstructorViewSet)
lesson_router.register(r'lessonattendrecord', views_lesson.LessonAttendRecordViewSet)

from flashsale.restpro.v2 import views_mama_v2, views_verifycode_login, views_packageskuitem

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name="rest_base.html")),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^lesson/', include(lesson_router.urls, namespace='lesson')),
    url(r'^lesson/snsauth/', views_lesson.WeixinSNSAuthJoinView.as_view()),
    url(r'^packageskuitem', views_packageskuitem.PackageSkuItemView.as_view()),

    url(r'^v1/', include('flashsale.restpro.v1.urls')),
    url(r'^v2/', include('flashsale.restpro.v2.urls')),
)
