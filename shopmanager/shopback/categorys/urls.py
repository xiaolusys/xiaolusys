from django.conf.urls.defaults import patterns, include, url
from shopback.categorys.views import crawFullCategories


urlpatterns = patterns('',
    url(r'^update/(?P<cid>[^/]+)/$',crawFullCategories,name='update_categories'),
)
  