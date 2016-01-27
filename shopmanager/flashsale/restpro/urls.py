# coding: utf-8


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
from . import views_coupon
from . import views_integral
from flashsale.pay.views_login import weixin_login,weixin_auth_and_redirect
from flashsale.complain.views import ComplainViewSet
from flashsale.push import views as views_push

from . import views_wuliu
from . import views_praise
from . import views_pro_ref
from . import views_xlmm
from . import views_mmadver
from . import views_wuliu_new
from . import views_cushops



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
router.register(r'integral', views_integral.UserIntegralViewSet)
router.register(r'integrallog', views_integral.UserIntegralLogViewSet)
router.register(r'usercoupons', views_coupon.UserCouponsViewSet)
router.register(r'cpntmpl', views_coupon.CouponTemplateViewSet)

router.register(r'share', views_share.CustomShareViewSet)
router.register(r'saleproduct', views_praise.SaleProductViewSet)
router.register(r'hotproduct', views_praise.HotProductViewSet)
router.register(r'prorefrcd', views_pro_ref.ProRefRcdViewSet)
router.register(r'calcuprorefrcd', views_pro_ref.CalcuProRefRcd)



router.register(r'xlmm', views_xlmm.XiaoluMamaViewSet)
router.register(r'carrylog', views_xlmm.CarryLogViewSet)
router.register(r'cashout', views_xlmm.CashOutViewSet)
# router.register(r'clickcount', views_xlmm.ClickCountViewSet)
router.register(r'shopping', views_xlmm.StatisticsShoppingViewSet)
router.register(r'mmadver', views_mmadver.XlmmAdvertisViewSet)
router.register(r'ninepic', views_mmadver.NinePicAdverViewSet)
router.register(r'cushop', views_cushops.CustomerShopsViewSet)
router.register(r'cushoppros', views_cushops.CuShopProsViewSet)
router.register(r'clicklog', views_xlmm.ClickViewSet)


router.register(r'wuliu', views_wuliu_new.WuliuViewSet)

# 推送相关
router.register(r'push', views_push.PushViewSet)


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
        url(r'^products/(?P<pk>[0-9]+)/snapshot$',
            views_product.ProductShareView.as_view(),
            name='product-snapshot'),
        url(r'^trades/(?P<pk>[0-9]+)/orders$',
            views_trade.SaleOrderViewSet.as_view({'get': 'list'}),
            name='saletrade-saleorder'),
        url(r'^trades/(?P<pk>[0-9]+)/orders/details$',
            views_trade.SaleOrderViewSet.as_view({'get': 'details'}),
            name='saleorder-details'),
        url(r'^trades/(?P<tid>[0-9]+)/orders/(?P<pk>[0-9]+)$',
            views_trade.SaleOrderViewSet.as_view({'get': 'retrieve'}),
            name='saleorder-detail'),

        url(r'^order/(?P<pk>[0-9]+)/confirm_sign$',
            views_trade.SaleOrderViewSet.as_view({'post': 'confirm_sign'}),
            name='confirm_sign_order'),

        url(r'^user/integral/',
            views_integral.UserIntegralViewSet.as_view({'get': 'list'}),
            name="user-intergral"),
        url(r'^user/integrallog/',
            views_integral.UserIntegralLogViewSet.as_view({'get': 'list'}),
            name="user-intergrallog"),
    ])

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name="rest_base.html")),
    url(r'^v1/', include(router_urls,namespace='v1')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^wuliu/',views_wuliu.WuliuView.as_view()),
    #url(r'^test/',views_wuliu.test),
)
