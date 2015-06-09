from django.conf.urls.defaults import patterns, url
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required  


from . import views


urlpatterns = patterns('',
    url(r'^$',views.landing),
    url(r'^m/$',views.MamaStatsView.as_view()),
    url(r'^stats/$',staff_member_required(views.StatsView.as_view())),
    url(r'^cashout/$',views.CashoutView.as_view()),
    url(r'^cashoutlist/$',views.CashOutList.as_view()),
    url(r'^carrylist/$',views.CarryLogList.as_view()),
    url(r'^(?P<linkid>\d+)/$',views.logclicks),    
    url(r'^charge/(?P<pk>\d+)/$',staff_member_required(views.chargeWXUser)),
    url(r'^xlmm/(?P<pk>\d+)/$', staff_member_required(views.XiaoluMamaModelView.as_view())),
    url(r'^cashoutverify/(?P<xlmm>\d+)/(?P<id>\d+)/$',staff_member_required(views.cash_Out_Verify),name="cashout_verify"),
    url(r'^cashmodify/(?P<data>\w+)/$',staff_member_required(views.cash_modify)), #
    url(r'^cashreject/(?P<data>\w+)/$',staff_member_required(views.cash_reject)), #
    url(r'^stats_summary/$',staff_member_required(views.stats_summary),name="stats_summary"),
    url(r'^mama_verify/$',staff_member_required(views.mama_Verify),name="mama_verify"),
    url(r'^mama_verify_action/$',staff_member_required(views.mama_Verify_Action),name="mama_verify_action"),

    url(r'^duokefu_customer/$',views.kf_Customer,name="kf_Customer"),
    url(r'^duokefu_search/$',views.kf_Search_Page,name="kf_Search_Page"),
    url(r'^duokefu_search_by_mobile/$',views.kf_Search_Order_By_Mobile,name="search_Order_By_Mobile"),
    url(r'^duokefu_weixin_order/$',views.kf_Weixin_Order,name="weixin_Order"),
    url(r'^duokefu_order_detail/$',views.kf_Search_Order_Detail,name="kf_Search_Order_Detail"),
    url(r'^duokefu_find_more/$',views.ke_Find_More_Weixin_Order,name="ke_Find_More_Weixin_Order"),


    url(r'^top50/click/$', views.xlmm_Click_Top, name="xlmm_Click_Top"),
    url(r'^top50/order/$',views.xlmm_Order_Top,name="xlmm_Order_Top"),
    url(r'^top50/conversion/$',views.xlmm_Conversion_Top, name="xlmm_Conversion_Top"),


    url(r'^top50/click/week/$', views.xlmm_Click_Top_Week, name="xlmm_Click_Top_Week"),
    url(r'^top50/order/week/$', views.xlmm_Order_Top_Week, name="xlmm_Order_Top_Week"),

    url(r'^top50/click/month/$', views.xlmm_Click_Top_Month, name="xlmm_Click_Top_Month"),
    url(r'^top50/order/month/$', views.xlmm_Order_Top_Month, name="xlmm_Order_Top_Month"),
    url(r'^top50/convers/month/$', views.xlmm_Convers_Top_Month, name="xlmm_Convers_Top_Month"),


)
