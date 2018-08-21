from django.conf.urls import include, url
from shopback.users.views import *

urlpatterns = [
    url(r'^username/$', get_usernames_by_segstr, name='usernames_by_segstr'),
]
