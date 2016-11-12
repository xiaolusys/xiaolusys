# coding:utf-8
from django.conf.urls import url, include
# from core.options.authentication import UserLoggedInAuthentication
# fangkaineng  7-29好像没有用这个方法，就删掉了
##    from core.options.views import InstanceModelView
from shopapp.autolist.views import *
# from core.options.permissions import IsAuthenticated, PerUserThrottling
from shopapp.autolist.views import ListItemTaskView, CreateListItemTaskModelView

# from shopapp.autolist.resources import ItemListTaskResource

urlpatterns = [
    url('^$', pull_from_taobao, name='pull_from_taobao'),
    url('itemlist/$', list_all_items, name='list_all_items'),
    url('timetable/$', show_time_table_summary, name='show_time_table_summary'),
    url('weektable/(?P<weekday>\d+)/$', show_weektable, name='show_weektable'),
    url('scheduletime/$', change_list_time, name='change_list_time'),
    url('timetablecats/$', show_timetable_cats, name='show_timetable_cats'),
    url('timeslots/$', get_timeslots_json, name='get_timeslots'),
    url('logs/$', show_logs, name='show_logs'),
    url('invalid/(?P<num_iid>[^/]+)/$', invalid_list_task, name='invalid_list'),

    url(r'^listtask/$', CreateListItemTaskModelView.as_view()),  # fang   2015  7-20
    # fang    7-29好像没有用这个方法，就删掉了
    #  url(r'^(?P<pk>[^/]+)/$', InstanceModelView.as_view(
    # resource=ItemListTaskResource,
    # authentication=(UserLoggedInAuthentication,),
    # permissions=(IsAuthenticated,)
    #        )),
    #  7-29好像没有用这个方法，就删掉了
    url(r'^list/self/$', ListItemTaskView.as_view(
       # resource=ItemListTaskResource,
       # authentication=(UserLoggedInAuthentication,),
       # permissions=(IsAuthenticated,),
    )),
]
