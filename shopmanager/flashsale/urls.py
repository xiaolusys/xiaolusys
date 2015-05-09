from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('',
    
#     (r'^supplier/',include('flashsale.supplier.urls')),
#     (r'^purchase/',include('flashsale.purchase.urls')),
#     (r'^pay/',include('flashsale.pay.urls')),
    (r'^dinghuo/',include('flashsale.dinghuo.urls')),
    (r'^clickcount/', include('flashsale.clickcount.urls')),
)
