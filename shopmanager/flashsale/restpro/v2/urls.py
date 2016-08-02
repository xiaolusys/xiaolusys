# coding: utf-8
from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from django.views.decorators.cache import cache_page
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework import routers

# 2016-3-2 v2
from flashsale.restpro.v2 import views_mama_v2, views_verifycode_login, views_packageskuitem
from flashsale.restpro.v2 import views_trade_v2, views_product_v2, views_category


v2_router = routers.DefaultRouter(trailing_slash=False)
v2_router.register(r'categorys', views_category.SaleCategoryViewSet)
v2_router.register(r'carts', views_trade_v2.ShoppingCartViewSet)
v2_router.register(r'products', views_product_v2.ProductViewSet)
v2_router.register(r'modelproducts', views_product_v2.ModelProductV2ViewSet)
v2_router.register(r'trades', views_trade_v2.SaleTradeViewSet)
v2_router.register(r'orders', views_trade_v2.SaleOrderViewSet)
v2_router.register(r'fortune', views_mama_v2.MamaFortuneViewSet)
v2_router.register(r'carry', views_mama_v2.CarryRecordViewSet)
v2_router.register(r'ordercarry', views_mama_v2.OrderCarryViewSet)
v2_router.register(r'awardcarry', views_mama_v2.AwardCarryViewSet)
v2_router.register(r'clickcarry', views_mama_v2.ClickCarryViewSet)
v2_router.register(r'activevalue', views_mama_v2.ActiveValueViewSet)
v2_router.register(r'referal', views_mama_v2.ReferalRelationshipViewSet)
v2_router.register(r'group', views_mama_v2.GroupRelationshipViewSet)
v2_router.register(r'visitor', views_mama_v2.UniqueVisitorViewSet)
v2_router.register(r'fans', views_mama_v2.XlmmFansViewSet)
v2_router.register(r'dailystats', views_mama_v2.DailyStatsViewSet)

from flashsale.restpro.v1 import views_coupon_new
v2_router.register(r'usercoupons', views_coupon_new.UserCouponsViewSet)
v2_router.register(r'cpntmpl', views_coupon_new.CouponTemplateViewSet)
v2_router.register(r'sharecoupon', views_coupon_new.OrderShareCouponViewSet)
v2_router.register(r'tmpsharecoupon', views_coupon_new.TmpShareCouponViewset)

v2_router.register(r'rank', views_rank.MamaCarryTotalViewSet)
v2_router.register(r'teamrank', views_rank.MamaTeamCarryTotalViewSet)
v2_router.register(r'message', views_message.XlmmMessageViewSet)

v2_router_urls = v2_router.urls
v2_router_urls += format_suffix_patterns([
    url(r'^mama/order_carry_visitor', views_mama_v2.OrderCarryVisitorView.as_view()),
    url(r'^send_code', views_verifycode_login.SendCodeView.as_view()),
    url(r'^verify_code', views_verifycode_login.VerifyCodeView.as_view()),
    url(r'^reset_password', views_verifycode_login.ResetPasswordView.as_view()),
    url(r'^passwordlogin', views_verifycode_login.PasswordLoginView.as_view()),
    url(r'^weixinapplogin', views_verifycode_login.WeixinAppLoginView.as_view()),
    url(r'^potential_fans', views_mama_v2.PotentialFansView.as_view()),
])

from flashsale.restpro.v2 import views_lesson
lesson_router = routers.DefaultRouter(trailing_slash=False)
lesson_router.register(r'lessontopic', views_lesson.LessonTopicViewSet)
lesson_router.register(r'lesson', views_lesson.LessonViewSet)
lesson_router.register(r'instructor', views_lesson.InstructorViewSet)
lesson_router.register(r'lessonattendrecord', views_lesson.LessonAttendRecordViewSet)

urlpatterns = patterns('',
    url(r'^', include(v2_router_urls, namespace='rest_v2')),
    url(r'^mama/', include(v2_router_urls)),
)