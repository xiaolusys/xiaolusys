from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('',
    (r'^hotkeys/$','subway.views.saveHotkeys'),
    (r'^sackeys/$','subway.views.selectAndCancleKeys'),
    (r'^keyscores/$','subway.views.saveOrUpdateKeyScores'),
    (r'^topkeys/$','subway.views.getValuableHotKeys'),
)
