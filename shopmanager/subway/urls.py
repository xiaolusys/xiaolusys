from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('subway.views',

    (r'^sackeys/$','selectAndCancleKeys'),
    (r'^keyscores/save/$','saveKeyScores'),
    #(r'^cookie/save/$','getSubwayCookie'),

    (r'^saveztcitem/$', 'saveZtcItem'),
    (r'^catkeys/$','getCatHotKeys'),
)

urlpatterns += patterns('subway.tc_views',
    (r'^taoci/update/$','updateTaociByCats'),
    (r'^taoci/getorupdate/$', 'getOrUpdateTaociKey'),
    (r'^taoci/recomend/hotkey/$','getRecommendHotKey'),
    (r'^taoci/recomend/newkey/$','getRecommendNewKey'),
)

urlpatterns += patterns('subway.lz_views',

    (r'^lzkey/update/$', 'updateLzKeysItems'),
    (r'^lzkey/getorupdate/$', 'getOrUpdateLiangZiKey'),
)
