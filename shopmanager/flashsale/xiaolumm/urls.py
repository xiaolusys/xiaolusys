from django.conf.urls.defaults import patterns, url
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required  
from django.views.generic import TemplateView

from . import views ,views_duokefu,views_top100_iter,views_xlmminfo,views_order_percent, top_view_api
from .views_register import MamaRegisterView,MamaConfirmView
from rest_framework import routers
from . import views_xlmm_active, views_xlmm_adver

urlpatterns = patterns('',
    url(r'^$',views.landing),
    url(r'^m/$',views.MamaStatsView.as_view(),name="mama_homepage"),
    url(r'^register/(?P<mama_id>\d+)/$',MamaRegisterView.as_view(),name="mama_register"),
    url(r'^register/confirm/$',MamaConfirmView.as_view(),name="mama_confirm"),
    url(r'^help/sharewx/$', TemplateView.as_view(template_name="mama_sharewx.html"), name='mama_sharewx'),
    url(r'^help/recruit/$', TemplateView.as_view(template_name="mama_recruit.html"), name='mama_recruit'),
    url(r'^help/term_service/$', TemplateView.as_view(template_name="term_service.html"), name='term_service'),
    url(r'^income/$',views.MamaIncomeDetailView.as_view()),
    
    url(r'^stats/$',staff_member_required(views.StatsView.as_view())),
    url(r'^cashout/$',views.CashoutView.as_view()),
    url(r'^cashoutlist/$',views.CashOutList.as_view()),
    url(r'^carrylist/$',views.CarryLogList.as_view()),
    url(r'^(?P<linkid>\d+)/$',views.logclicks), 
    url(r'^channel/(?P<linkid>\d+)/$',views.logChannelClicks),     
    url(r'^charge/(?P<pk>\d+)/$',staff_member_required(views.chargeWXUser)),
    url(r'^xlmm/(?P<pk>\d+)/$', staff_member_required(views.XiaoluMamaModelView.as_view())),
    url(r'^cashoutverify/(?P<xlmm>\d+)/(?P<id>\d+)/$',staff_member_required(views.cash_Out_Verify),name="cashout_verify"),
    url(r'^cashmodify/(?P<data>\w+)/$',staff_member_required(views.cash_modify)), #
    url(r'^cashreject/(?P<data>\w+)/$',staff_member_required(views.cash_reject)), #
    url(r'^stats_summary/$',staff_member_required(views.stats_summary),name="stats_summary"),
    url(r'^mama_verify_action/$',staff_member_required(views.mama_Verify_Action),name="mama_verify_action"),

    url(r'^duokefu_customer/$',views_duokefu.kf_Customer,name="kf_Customer"),
    url(r'^duokefu_search/$',views_duokefu.kf_Search_Page,name="kf_Search_Page"),
    url(r'^duokefu_search_by_mobile/$',views_duokefu.kf_Search_Order_By_Mobile,name="search_Order_By_Mobile"),
    url(r'^duokefu_weixin_order/$',views_duokefu.kf_Weixin_Order,name="weixin_Order"),
    url(r'^duokefu_order_detail/$',views_duokefu.kf_Search_Order_Detail,name="kf_Search_Order_Detail"),
    url(r'^duokefu_find_more/$',views_duokefu.ke_Find_More_Weixin_Order,name="ke_Find_More_Weixin_Order"),
    #url(r'^duokefu_logistics/$',views_duokefu.kf_Logistics,name="kf_Logistics"),
    
    # ITER TOP100
    url(r'^top100/click/month/$', views_top100_iter.Top100_Click, name="Top100_Click"),
    url(r'^top100/order/month/$', views_top100_iter.Top100_Order, name="Top100_Click"),

    # mama data search
    url(r'^xlmm_info/$', staff_member_required(views_xlmminfo.XlmmInfo.as_view()), name="MamaAll"),
    url(r'^xlmm_exit/$', staff_member_required(views_xlmminfo.xlmmExitAction), name="MamaAll"),
    # order analysis in different linkid
    url(r'^order_linkid_analysis/$', staff_member_required(views_order_percent.by_Linkid_Analysis), name="by_Linkid_Analysis"),
    url(r'^order_linkid_showpage/$', staff_member_required(views_order_percent.show_Orderlink_Page), name="by_Linkid_Analysis"),
    url(r'^order_carry_analysis/$', staff_member_required(views_order_percent.xlmm_Carry_Log), name="xlmm_Carry_Log"),
    
    url(r'^top/', staff_member_required(top_view_api.TopDataView.as_view()), name="xlmm_tp_api"),
    url(r'^xlmm_active/', staff_member_required(views_xlmm_active.XlmmActive.as_view()), name="xlmm_active"),
    url(r'^adver_nine_pic/', staff_member_required(views_xlmm_adver.NinepicView.as_view()), name="nine_pic"),


)