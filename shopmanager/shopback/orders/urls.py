from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('shopback.orders.views',

   url('amount/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','update_finish_trade_amount',name='finish_trade_amount'),
   url('increment/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','update_increment_trade',name='increment_trade'),
)
  