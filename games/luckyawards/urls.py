from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from django.views.decorators.cache import cache_page

from rest_framework.urlpatterns import format_suffix_patterns

from . import views

urlpatterns = patterns('',
                       url(r'^awards/', views.LuckyAwardView.as_view(), name="lucky-awards"),
                       )
