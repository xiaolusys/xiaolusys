# -*- coding:utf8 -*-
from django.conf.urls import include, url
from django.views.decorators.csrf import csrf_exempt
from shopapp.calendar.views import MainEventPageView, StaffEventView, delete_staff_event, complete_staff_event
# from shopapp.calendar.renderers import CalendarTempalteRenderer
# from shopapp.calendar.resources import MainStaffEventResource,StaffEventResource

from shopback.base.authentication import login_required_ajax

urlpatterns = [
    url(r'delete/(?P<id>\d{1,20})/', csrf_exempt(login_required_ajax(delete_staff_event))),
    url(r'complete/(?P<id>\d{1,20})/', csrf_exempt(login_required_ajax(complete_staff_event))),
    url(r'^$', MainEventPageView.as_view(
       # resource=MainStaffEventResource,
       # renderers=(CalendarTempalteRenderer,),
       #  authentication=(UserLoggedInAuthentication,),
       #  permissions=(IsAuthenticated,)
    )),
    url(r'^events/$', StaffEventView.as_view(
       # resource=StaffEventResource,
       #  renderers=(BaseJsonRenderer,),
       # authentication=(UserLoggedInAuthentication,),
       # permissions=(IsAuthenticated,)
    )),
]
