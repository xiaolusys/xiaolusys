from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from django.views.decorators.cache import cache_page
from rest_framework.urlpatterns import format_suffix_patterns

from rest_framework import routers
from . import views
from . import views_user
from . import views_product 
from . import views_trade 
from . import views_share
from flashsale.pay.views_login import weixin_login,weixin_auth_and_redirect
from flashsale.complain.views import ComplainViewSet

from . import views_wuliu

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'complain', ComplainViewSet)
router.register(r'register', views_user.RegisterViewSet)
router.register(r'users', views_user.CustomerViewSet)

router.register(r'posters', views_product.PosterViewSet)
router.register(r'products', views_product.ProductViewSet)
router.register(r'carts', views_trade.ShoppingCartViewSet)
router.register(r'trades', views_trade.SaleTradeViewSet)
router.register(r'wxorders', views_trade.WXOrderViewSet)

router.register(r'refunds', views.SaleRefundViewSet)
router.register(r'address', views.UserAddressViewSet)
router.register(r'districts', views.DistrictViewSet)
router.register(r'integral', views.UserIntegralViewSet)
router.register(r'integrallog', views.UserIntegralLogViewSet)
router.register(r'couponpool', views.UserCouponPoolViewSet)
router.register(r'usercoupons', views.UserCouponsViewSet)

router.register(r'share', views_share.CustomShareViewSet)

router_urls = router.urls

router_urls += format_suffix_patterns([  
        url(r'^users/weixin_login/$',weixin_login,name='weixin-login'),    
        url(r'^users/weixin_auth/$',weixin_auth_and_redirect,name='xlmm-wxauth'), 
        url(r'^products/modellist/(?P<model_id>[0-9]+)$',
            views_product.ProductViewSet.as_view({'get': 'modellist'}),
            name='product-model-list'),
        url(r'^products/preview_modellist/(?P<model_id>[0-9]+)$',
            views_product.ProductViewSet.as_view({'get': 'preview_modellist'}),
            name='product-model-list'),
        url(r'^trades/(?P<pk>[0-9]+)/orders$',
            views_trade.SaleOrderViewSet.as_view({'get': 'list'}),
            name='saletrade-saleorder'),
        url(r'^trades/(?P<pk>[0-9]+)/orders/details$',
            views_trade.SaleOrderViewSet.as_view({'get': 'details'}),
            name='saleorder-details'),
        url(r'^trades/(?P<tid>[0-9]+)/orders/(?P<pk>[0-9]+)$',
            views_trade.SaleOrderViewSet.as_view({'get': 'retrieve'}),
            name='saleorder-detail'),
        url(r'^user/integral/',
            views.UserIntegralViewSet.as_view({'get': 'list'}),
            name="user-intergral"),
        url(r'^user/integrallog/',
            views.UserIntegralLogViewSet.as_view({'get': 'list'}),
            name="user-intergrallog"),
    ])

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name="rest_base.html")),
    url(r'^v1/', include(router_urls,namespace='v1')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^wuliu/',views_wuliu.WuliuView.as_view()),
    url(r'^test/',views_wuliu.test),
)


