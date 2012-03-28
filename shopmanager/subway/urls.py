from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('subway.views',
    (r'^hotkeys/$','saveHotkeys'),
    (r'^sackeys/$','selectAndCancleKeys'),
    (r'^keyscores/$','saveOrUpdateKeyScores'),
    (r'^topkeys/$','getValuableHotKeys'),
    (r'^cookie/save/$','getSubwayCookie'),

    (r'^saveztcitem/$', 'saveZtcItem'),
    (r'^catkeys/$','getCatHotKeys'),
)

urlpatterns += patterns('subway.tc_views',
    (r'^taoci/update/$','updateTaociByCats'),
    (r'^taoci/getorupdate/$', 'getOrUpdateTaociKey'),
    (r'^taoci/recomend/$','getRecommendNewAndHotKey'),
)

urlpatterns += patterns('subway.lz_views',

    (r'^lzkey/update/$', 'updateLzKeysItems'),
    (r'^lzkey/getorupdate/$', 'getOrUpdateLiangZiKey'),
)
