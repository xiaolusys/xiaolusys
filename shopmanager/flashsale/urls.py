from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('',
    
#     (r'^supplier/',include('flashsale.supplier.urls')),
#     (r'^purchase/',include('flashsale.purchase.urls')),
    (r'^pay/',include('flashsale.pay.urls')),
    (r'^rebeta/',include('flashsale.clickrebeta.urls')),
)
