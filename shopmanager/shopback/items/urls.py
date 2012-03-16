from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('shopback.items.views',

    url('update/$','updateItems',name='update_items'),

)
