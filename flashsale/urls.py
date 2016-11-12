from django.conf.urls import patterns, include

urlpatterns = patterns(
    '',
    (r'^complain/', include('flashsale.complain.urls')),
    (r'^dinghuo/', include('flashsale.dinghuo.urls')),
    (r'^rebeta/', include('flashsale.clickrebeta.urls')),
    (r'^exam/', include('flashsale.mmexam.urls')),
    (r'^daystats/', include('flashsale.daystats.urls')),
    (r'^kefu/', include('flashsale.kefu.urls')),
    (r'^promotion/', include('flashsale.promotion.urls')),
    (r'^apprelease/', include('flashsale.apprelease.urls')),
    (r'^finance/', include('flashsale.finance.urls')),
    (r'^weixingroup/',include('games.weixingroup.urls')),
    (r'^workorder/', include('flashsale.workorder.urls'))
)

