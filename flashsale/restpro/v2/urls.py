# coding: utf-8
from django.conf.urls import include, url
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

# 2016-3-2 v2
from . import views
from .views.kdn import KdnView
from flashsale.xiaolumm.views import views_rank, views_message, award, week_rank
from flashsale.pay.views import teambuy

v2_router = routers.DefaultRouter(trailing_slash=False)
v2_router.register(r'categorys', views.SaleCategoryViewSet)
v2_router.register(r'carts', views.ShoppingCartViewSet)
v2_router.register(r'products', views.ProductViewSet)
v2_router.register(r'modelproducts', views.ModelProductV2ViewSet)
v2_router.register(r'trades', views.SaleTradeViewSet)
v2_router.register(r'orders', views.SaleOrderViewSet)
v2_router.register(r'fortune', views.MamaFortuneViewSet)
v2_router.register(r'carry', views.CarryRecordViewSet)
v2_router.register(r'ordercarry', views.OrderCarryViewSet)
v2_router.register(r'awardcarry', views.AwardCarryViewSet)
v2_router.register(r'clickcarry', views.ClickCarryViewSet)
v2_router.register(r'activevalue', views.ActiveValueViewSet)
v2_router.register(r'referal', views.ReferalRelationshipViewSet)
v2_router.register(r'group', views.GroupRelationshipViewSet)
v2_router.register(r'visitor', views.UniqueVisitorViewSet)
v2_router.register(r'fans', views.XlmmFansViewSet)
v2_router.register(r'dailystats', views.DailyStatsViewSet)
v2_router.register(r'teambuy', teambuy.TeamBuyViewSet)
v2_router.register(r'express', views.WuliuViewSet)
v2_router.register(r'checkin', views.CheckinViewSet)
v2_router.register(r'qrcode', views.QRcodeViewSet)
v2_router.register(r'exchgorder', views.CouponExchgOrderViewSet)

from flashsale.restpro.v1 import views_coupon_new
from flashsale.restpro.v2 import views

v2_router.register(r'usercoupons', views_coupon_new.UserCouponsViewSet)
v2_router.register(r'cpntmpl', views_coupon_new.CouponTemplateViewSet)
v2_router.register(r'sharecoupon', views_coupon_new.OrderShareCouponViewSet)
v2_router.register(r'tmpsharecoupon', views_coupon_new.TmpShareCouponViewset)


# v2_router.register(r'rank', views_rank.MamaCarryTotalViewSet)
# v2_router.register(r'teamrank', views_rank.MamaTeamCarryTotalViewSet)
v2_router.register(r'rank', week_rank.WeekMamaCarryTotalViewSet)
v2_router.register(r'teamrank', week_rank.WeekMamaTeamCarryTotalViewSet)
v2_router.register(r'acrank', week_rank.ActivityMamaCarryTotalViewSet)
v2_router.register(r'acteamrank', week_rank.ActivityMamaTeamCarryTotalViewSet)
v2_router.register(r'message', views_message.XlmmMessageViewSet)
v2_router.register(r'award', award.PotentialMamaAwardViewset)
v2_router.register(r'mission', views.MamaMissionRecordViewset)
v2_router.register(r'trancoupon', views.CouponTransferRecordViewSet)

v2_router_urls = v2_router.urls
v2_router_urls += format_suffix_patterns([
    url(r'^mama/order_carry_visitor', views.OrderCarryVisitorView.as_view()),
    url(r'^send_code', views.SendCodeView.as_view()),
    url(r'^verify_code', views.VerifyCodeView.as_view()),
    url(r'^reset_password', views.ResetPasswordView.as_view()),
    url(r'^passwordlogin', views.PasswordLoginView.as_view()),
    url(r'^weixinapplogin', views.WeixinAppLoginView.as_view()),
    url(r'^potential_fans', views.PotentialFansView.as_view()),
    url(r'^request_cashout_verify_code', views.RequestCashoutVerifyCode.as_view()),
    url(r'^administrator', views.xiaolumm.MamaAdministratorViewSet.as_view()),
    url(r'^kdn', KdnView.as_view()),
    url(r'^activate', views.xiaolumm.ActivateMamaView.as_view()),
    url(r'^cashout_to_app', views.xiaolumm.CashOutToAppView.as_view()),
    url(r'^cashout_policy', views.xiaolumm.CashOutPolicyView.as_view()),
    url(r'^redirect_activity_entry', views.xiaolumm.RedirectActivityEntryView.as_view()),
    url(r'^redirect_stats_link', views.xiaolumm.RedirectStatsLinkView.as_view()),
    url(r'^recruit_elite_mama', views.xiaolumm.RecruitEliteMamaView.as_view()),
    url(r'^enable_elite_coupon', views.xiaolumm.EnableEliteCouponView.as_view()),
    url(r'^urlredirect', views.URLRedirectViewSet.as_view({'get': 'redirect'})),
    url(r'^wdt/logistics', views.WangDianTongViewSet.as_view({'post': 'logistics'})),
])

from flashsale.restpro.v2 import views

lesson_router = routers.DefaultRouter(trailing_slash=False)
lesson_router.register(r'lessontopic', views.LessonTopicViewSet)
lesson_router.register(r'lesson', views.LessonViewSet)
lesson_router.register(r'instructor', views.InstructorViewSet)
lesson_router.register(r'lessonattendrecord', views.LessonAttendRecordViewSet)

urlpatterns = [
    url(r'^', include(v2_router_urls, namespace='rest_v2')),
    url(r'^mama/', include(v2_router_urls)),
]
