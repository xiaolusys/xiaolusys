from django.conf.urls.defaults import patterns, include, url



urlpatterns = patterns('',

    (r'^taobao/rank/','search.views.getShopsRank'),
    (r'^rank/chart/$','search.views.genPeroidChart'),
    (r'^rank/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','search.views.genPageRankPivotChart'),

)
  