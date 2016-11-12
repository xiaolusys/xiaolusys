from django.conf.urls import include, url

urlpatterns = [
    #     (r'^supplier/',include('flashsale.supplier.urls')),
    #     (r'^purchase/',include('flashsale.purchase.urls')),
    #     (r'^pay/',include('flashsale.pay.urls')),
    url(r'^complain/', include('flashsale.complain.urls')),
    url(r'^dinghuo/', include('flashsale.dinghuo.urls')),
    url(r'^rebeta/', include('flashsale.clickrebeta.urls')),
    url(r'^exam/', include('flashsale.mmexam.urls')),
    url(r'^daystats/', include('flashsale.daystats.urls')),
    url(r'^kefu/', include('flashsale.kefu.urls')),
    url(r'^promotion/', include('flashsale.promotion.urls')),
    url(r'^apprelease/', include('flashsale.apprelease.urls')),
    url(r'^finance/', include('flashsale.finance.urls')),
    url(r'^weixingroup/',include('games.weixingroup.urls')),
    url(r'^workorder/', include('flashsale.workorder.urls'))
]

