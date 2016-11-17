# -*- coding:utf8 -*-
from django.conf.urls import include, url
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from shopapp.calendar.views import MainEventPageView, StaffEventView, delete_staff_event, complete_staff_event


from shopback.base.authentication import login_required_ajax

urlpatterns = [
    url(r'^index/', TemplateView.as_view(template_name="fullcalendar/default.html")),
    url(r'delete/(?P<id>\d{1,20})/', csrf_exempt(login_required_ajax(delete_staff_event))),
    url(r'complete/(?P<id>\d{1,20})/', csrf_exempt(login_required_ajax(complete_staff_event))),
    url(r'^$', MainEventPageView.as_view()),
    url(r'^events/$', StaffEventView.as_view()),
]
