from django.conf.urls import patterns, include, url

urlpatterns = patterns('shopback.users.views',

                       url(r'^username/$', 'get_usernames_by_segstr', name='usernames_by_segstr'),
                       )
