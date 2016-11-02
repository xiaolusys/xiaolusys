from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    
    (r'^wavepick/',include('supplychain.wavepick.urls')),
    (r'^supplier/', include('supplychain.supplier.urls')),
    (r'^category/', include('supplychain.category.urls')),
   # (r'^temai/',include('supplychain.temai.urls')),
)
