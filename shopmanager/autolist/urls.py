from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('autolist.views',
    url('pull/$','pull_from_taobao',name='pull_from_taobao'),
    #url('push/$','push_to_taobao',name='pull_to_taobao'),
    url('itemlist/$','list_all_items',name='list_all_items'),
    url('timetable/$','show_time_table',name='show_time_table'),
    url('changetime/$','change_list_time',name='change_list_time'),
)
