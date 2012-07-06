from django.conf.urls.defaults import patterns, url,include
from shopback.base.authentication import UserLoggedInAuthentication
from shopback.base.views import InstanceModelView
from shopback.base.permissions import IsAuthenticated, PerUserThrottling
from shopapp.autolist.views import direct_update_listing,direct_del_listing,ListItemTaskView,CreateListItemTaskModelView
from shopapp.autolist.resources import ItemListTaskResource

urlpatterns = patterns('shopapp.autolist.views',
    url('^$','pull_from_taobao',name='pull_from_taobao'),
    url('itemlist/$','list_all_items',name='list_all_items'),
    url('timetable/$','show_time_table_summary',name='show_time_table_summary'),
    url('scheduletime/$','change_list_time',name='change_list_time'),
    url('timetablecats/$','show_timetable_cats',name='show_timetable_cats'),
    url('logs/$', 'show_logs', name='show_logs'),

    url(r'^update/(?P<num_iid>[^/]+)/(?P<num>[^/]+)/$',direct_update_listing,name='update_listing'),
    url(r'^delete/(?P<num_iid>[^/]+)/$',direct_del_listing,name='delete_listing'),
    url(r'^listtask/$', CreateListItemTaskModelView.as_view(resource=ItemListTaskResource, authentication=(UserLoggedInAuthentication,), permissions=(IsAuthenticated,),)),
    url(r'^(?P<pk>[^/]+)/$', InstanceModelView.as_view(resource=ItemListTaskResource, authentication=(UserLoggedInAuthentication,), permissions=(IsAuthenticated,))),
    url(r'^list/self/$', ListItemTaskView.as_view(resource=ItemListTaskResource, authentication=(UserLoggedInAuthentication,), permissions=(IsAuthenticated,),)),
    url(r'^djcelery/',include('djcelery.urls'),name="task_state")
)
