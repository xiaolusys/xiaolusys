__author__ = 'meixqhi'
from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('shopapp.comments.views',

    url('ignore/(?P<id>[^/]+)/$','comment_not_need_explain',name='comment_ignore'),
    url('explain/$','explain_for_comment',name='comment_explain')
)
