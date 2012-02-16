from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('autolist.views',
    url('pull/$','pull_from_taobao',name='pull_from_taobao'),
    url('^$','pull_from_taobao',name='pull_from_taobao'),
    url('itemlist/$','list_all_items',name='list_all_items'),
    url('timetable/$','show_time_table_summary',name='show_time_table_summary'),
    url('scheduletime/$','change_list_time',name='change_list_time'),
    url('timetablecats/$','show_timetable_cats',name='show_timetable_cats'),
    url('logs/$', 'show_logs', name='show_logs'),
)
