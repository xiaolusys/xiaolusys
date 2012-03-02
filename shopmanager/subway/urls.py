from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('',
    (r'^hotkeys/$','subway.views.saveHotkeys'),
    (r'^keyscores/$','subway.views.saveKeyScores'),
    (r'^topkeys/$','subway.views.getValuableHotKeys'),
)
