from django.conf.urls import include, url


urlpatterns = [
    # url(r'^wavepick/',include('pms.wavepick.urls')),
    url(r'^supplier/', include('pms.supplier.urls')),
    # url(r'^category/', include('pms.category.urls')),
   # (r'^temai/',include('pms.temai.urls')),
]
