from django.conf.urls.defaults import patterns, include, url
from shopback.categorys.views import crawFullCategories,getCategoryIds,getCategoryTree


urlpatterns = patterns('',
    url(r'^update/(?P<cid>[^/]+)/$',crawFullCategories,name='update_categories'),
    url(r'^cats_by_name/$',getCategoryIds,name='get_cats_by_name'),
    url(r'^cats_tree/$',getCategoryTree,name='get_cats_tree')
)
  