from django.conf.urls import include, url


urlpatterns = [
    url(r'^wavepick/',include('supplychain.wavepick.urls')),
    url(r'^supplier/', include('supplychain.supplier.urls')),
    url(r'^category/', include('supplychain.category.urls')),
   # (r'^temai/',include('supplychain.temai.urls')),
]
