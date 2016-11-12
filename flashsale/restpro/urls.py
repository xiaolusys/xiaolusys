# coding: utf-8

from django.conf.urls import include, url
from django.views.generic.base import TemplateView
from django.views.decorators.cache import cache_page
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework import routers
from flashsale.restpro.v1 import views
from flashsale.restpro.v1 import views_user
from flashsale.restpro.v1 import views_product
from flashsale.restpro.v1 import views_trade
from flashsale.restpro.v1 import views_share
from flashsale.restpro.v1 import views_coupon_new
from flashsale.restpro.v1 import views_integral
from flashsale.restpro.v1 import views_portal
from flashsale.restpro.v1 import views_wuliu
from flashsale.restpro.v1 import views_praise
from flashsale.restpro.v1 import views_pro_ref
from flashsale.restpro.v1 import views_xlmm
from flashsale.restpro.v1 import views_mmadver
from flashsale.restpro.v1 import views_wuliu_new
from flashsale.restpro.v1 import views_return_wuliu
from flashsale.restpro.v1 import views_cushops
from flashsale.restpro.v1 import views_promotion
from flashsale.restpro.v1 import views_login_v2
from flashsale.restpro.v1 import views_faqs
from flashsale.restpro.v1 import views_mmexams
from flashsale.restpro.v1 import views_favorites
from flashsale.pay.views import weixin_login, weixin_test, weixin_auth_and_redirect
from flashsale.complain.views import ComplainViewSet
from flashsale.push import views as views_push

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'complain', ComplainViewSet)
router.register(r'register', views_user.RegisterViewSet)
router.register(r'users', views_user.CustomerViewSet)

router.register(r'posters', views_product.PosterViewSet)
router.register(r'products', views_product.ProductViewSet)
router.register(r'activitys', views_product.ActivityViewSet)
router.register(r'carts', views_trade.ShoppingCartViewSet)
router.register(r'favorites', views_favorites.FavoritesViewSet)
router.register(r'trades', views_trade.SaleTradeViewSet)
router.register(r'wxorders', views_trade.WXOrderViewSet)
router.register(r'portal', views_portal.PortalViewSet)
router.register(r'brands', views_portal.BrandEntryViewSet)


router.register(r'refunds', views.SaleRefundViewSet)
router.register(r'address', views.UserAddressViewSet)
router.register(r'districts', views.DistrictViewSet)
router.register(r'integral', views_integral.UserIntegralViewSet)
router.register(r'integrallog', views_integral.UserIntegralLogViewSet)
router.register(r'usercoupons', views_coupon_new.UserCouponsViewSet)
router.register(r'cpntmpl', views_coupon_new.CouponTemplateViewSet)

router.register(r'share', views_share.CustomShareViewSet)
router.register(r'saleproduct', views_praise.SaleProductViewSet)
router.register(r'hotproduct', views_praise.HotProductViewSet)
router.register(r'prorefrcd', views_pro_ref.ProRefRcdViewSet)
router.register(r'calcuprorefrcd', views_pro_ref.CalcuProRefRcd)
router.register(r'download', views.AppDownloadLinkViewSet)
router.register(r'faqs', views_faqs.SaleCategoryViewSet)
router.register(r'mmexam', views_mmexams.MmexamsViewSet)
router.register(r'mmwebviewconfig', views_mmadver.MamaVebViewConfViewSet)

#  推广接口注册
promotion_router = routers.DefaultRouter(trailing_slash=False)
promotion_router.register(r'xlmm', views_xlmm.XiaoluMamaViewSet)
promotion_router.register(r'carrylog', views_xlmm.CarryLogViewSet)
promotion_router.register(r'cashout', views_xlmm.CashOutViewSet)
# router.register(r'clickcount', views_xlmm.ClickCountViewSet)
promotion_router.register(r'shopping', views_xlmm.StatisticsShoppingViewSet)
promotion_router.register(r'mmadver', views_mmadver.XlmmAdvertisViewSet)
promotion_router.register(r'ninepic', views_mmadver.NinePicAdverViewSet)
promotion_router.register(r'cushop', views_cushops.CustomerShopsViewSet)
promotion_router.register(r'cushoppros', views_cushops.CuShopProsViewSet)
promotion_router.register(r'clicklog', views_xlmm.ClickViewSet)
promotion_router.register(r'free_proinfo', views_promotion.XLFreeSampleViewSet)
promotion_router.register(r'free_order', views_promotion.XLSampleOrderViewSet)
promotion_router.register(r'fanlist', views_promotion.InviteReletionshipView)

router.register(r'wuliu', views_wuliu_new.WuliuViewSet)
router.register(r'rtnwuliu', views_return_wuliu.ReturnWuliuViewSet)

# 推送相关
router.register(r'push', views_push.PushViewSet)

router_urls = router.urls
router_urls_promotion = promotion_router.urls

router_urls += format_suffix_patterns([
    url(r'^users/weixin_login/$', weixin_login, name='weixin-login'),
    url(r'^users/weixin_test/$', weixin_test, name='weixin-test'),
    url(r'^users/weixin_auth/$', weixin_auth_and_redirect, name='xlmm-wxauth'),

    url(r'^products/modellist/(?P<model_id>[0-9]+)$',
        views_product.ProductViewSet.as_view({'get': 'modellist'}),
        name='product-model-list'),
    url(r'^products/preview_modellist/(?P<model_id>[0-9]+)$',
        views_product.ProductViewSet.as_view({'get': 'preview_modellist'}),
        name='product-model-list'),
    url(r'^products/(?P<pk>[0-9]+)/snapshot$',
        views_product.ProductShareView.as_view(),
        name='product-snapshot'),
    url(r'^brands/(?P<brand_id>[0-9]+)/products$',
        views_portal.BrandProductViewSet.as_view({'get': 'list'}),
        name='brand-product'),

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
    url(r'^users/integral',
        views_integral.UserIntegralViewSet.as_view({'get': 'list'}),
        name="user-intergral"),
    url(r'^users/integrallog',
        views_integral.UserIntegralLogViewSet.as_view({'get': 'list'}),
        name="user-intergrallog"),
    url(r'^users/(?P<pk>[0-9]+)/bang_budget',
        views_user.UserBugetBangView.as_view(),
        name="user-budget-bang"),

    url(r'^address/(?P<pk>[0-9]+)/update',
        views.UserAddressViewSet.as_view({'post': 'update'}),
        name="address-update"),
])


from flashsale.restpro.v2 import views as views_v2

lesson_router = routers.DefaultRouter(trailing_slash=False)
lesson_router.register(r'lessontopic', views_v2.LessonTopicViewSet)
lesson_router.register(r'lesson', views_v2.LessonViewSet)
lesson_router.register(r'instructor', views_v2.InstructorViewSet)
lesson_router.register(r'lessonattendrecord', views_v2.LessonAttendRecordViewSet)


urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name="rest_base.html")),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^lesson/', include(lesson_router.urls, namespace='lesson')),
    url(r'^lesson/snsauth/', views_v2.WeixinSNSAuthJoinView.as_view()),
    url(r'^packageskuitem', views_v2.PackageSkuItemView.as_view()),

    url(r'^v1/', include('flashsale.restpro.v1.urls')),
    url(r'^v2/', include('flashsale.restpro.v2.urls')),
]
