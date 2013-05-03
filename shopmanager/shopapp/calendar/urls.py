#-*- coding:utf8 -*-
from django.conf.urls import patterns
from shopapp.calendar.views import MainEventPageView,StaffEventView
from shopapp.calendar.renderers import CalendarTempalteRenderer
from shopapp.calendar.resources import MainStaffEventResource
from shopback.base.permissions import IsAuthenticated
from shopback.base.authentication import UserLoggedInAuthentication,login_required_ajax

urlpatterns = patterns('',
    (r'^', MainEventPageView.as_view(
        resource=MainStaffEventResource,
        renderers=(CalendarTempalteRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
)