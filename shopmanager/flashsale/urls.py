from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    '',

    #     (r'^supplier/',include('flashsale.supplier.urls')),
    #     (r'^purchase/',include('flashsale.purchase.urls')),

    #     (r'^pay/',include('flashsale.pay.urls')),
    (r'^complain/', include('flashsale.complain.urls')),
    (r'^dinghuo/', include('flashsale.dinghuo.urls')),
    #     (r'^clickcount/', include('flashsale.clickcount.urls')),
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

