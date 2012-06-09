from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('shopback.orders.views',

   url('amount/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','update_finish_trade_amount',name='finish_trade_amount'),
   url('interval/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','update_interval_trade',name='interval_trade'),

   url('logistics/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','update_interval_logistics',name='update_logistic'),
   url('refund/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','update_interval_refunds',name='interval_refund'),

   url('reportform/$','gen_report_form_file',name='gen_report_form_file'),
)
  