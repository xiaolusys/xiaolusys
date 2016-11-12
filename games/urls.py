from django.conf.urls import include, url


urlpatterns = [
    url(r'^paint/', include('games.paint.urls')),
    url(r'^weixingroup/', include('games.weixingroup.urls')),
    url(r'^renew/', include('games.renewremind.urls')),
]
