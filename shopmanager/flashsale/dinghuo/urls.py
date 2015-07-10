# coding:utf-8
from django.conf.urls import include, url
from flashsale.dinghuo import views
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .views import DailyDingHuoStatsView, StatsByProductIdView, DailyWorkView
from django.views.decorators.csrf import csrf_exempt
from .views_change_detail import ChangeDetailView, AutoNewOrder, change_inferior_num
from .views_data_stats import DailyStatsView, StatsProductView, StatsSupplierView
from .view_daily_work import DailyDingHuoView, DailyDingHuoView2, ShowPicView
from .point_every_day import RecordPointView

urlpatterns = [

    url(r'^searchproduct/$', views.search_product, name='searchProduct'),       #搜索所有的商品 ajax
    url(r'^initdraft/$', views.init_draft, name='init_draft'),                   #初始化草稿箱
    url(r'^dingdan/$', views.new_order, name="new_order"),                     #订单页面填写完成后跳转
    url(r'^delcaogao/$', views.del_draft, name="delcaogao"),                   #删除所有草稿
    url(r'^data-chart/$', views.data_chart, name="data-chart"),
    url(r'^adddetail/(?P<outer_id>\d+)$', views.add_purchase, name="adddetail"),
    url(r'^plusquantity/$', views.plus_quantity, name="plusquantity"),          #增加草稿里面的一个商品的数量
    url(r'^plusordertail/$', views.plusordertail, name="plusordertail"),          #增加订单详情里面的一个商品的数量
    url(r'^minusordertail/$', views.minusordertail, name="minusordertail"),          #减少订单详情里面的一个商品的数量
    url(r'^minusarrivedquantity/$', views.minusarrived, name="minusarrivedquantity"),          #减少
    url(r'^minusquantity/$', views.minusquantity, name="minusquantity"),       #减少草稿里面的一个商品的数量
    url(r'^removedraft/$', views.removedraft, name="removedraft"),             #删除草稿里面的一个商品
    url(r'^detail/(?P<orderdetail_id>\d+)/$', views.viewdetail, name="mydetail"),
    url(r'^detaillayer/(?P<orderdetail_id>\d+)/$', views.detaillayer, name="detaillayer"),
    url(r'^changestatus/$', views.changestatus, name="changestatus"),
    url(r'^changedetail/(?P<order_detail_id>\d+)/$',csrf_exempt(staff_member_required(ChangeDetailView.as_view())), name="changedetail"),
    url(r'^daily/', staff_member_required(DailyDingHuoStatsView.as_view()), name="daily_ding_huo_stats"),  #大货每天统计
    url(r'^changearrivalquantity/$', views.changearrivalquantity, name="changearrivalquantity"),
    url(r'^statsbypid/(?P<product_id>\d+)/$', staff_member_required(StatsByProductIdView.as_view()), name="statsbypid"),  #根据商品id统计大货
    url(r'^dailywork/', staff_member_required(DailyWorkView.as_view()), name="dailywork"),  #大货任务
    url(r'^setusertogroup/$', views.setusertogroup, name="setusertogroup"),
    url(r'^adddetailtodinghuo/$', views.add_detail_to_ding_huo, name="add_detail_to_ding_huo"),
    url(r'^changeorderlist/$', views.modify_order_list, name="modify_order_list"),
    url(r'^auto_new_order/(?P<order_list_id>\d+)/$', AutoNewOrder.as_view(), name="auto_new_order"),
    url(r'^change_inferior_num/$', change_inferior_num, name="change_inferior_num"),
    url(r'^daily_stats/(?P<prev_day>\d+)/$', staff_member_required(DailyStatsView.as_view()), name="daily_stats"),
    url(r'^daily_work/$', staff_member_required(DailyDingHuoView.as_view()), name="dailywork2"),
    url(r'^stats_product/$', staff_member_required(StatsProductView.as_view()), name="stats_product"),
    url(r'^stats_supplier/$', staff_member_required(StatsSupplierView.as_view()), name="stats_supplier"),
    url(r'^point_every_day/$', csrf_exempt(staff_member_required(RecordPointView.as_view())), name="point_every_day"),
    url(r'^begin_ding_huo/$', staff_member_required(DailyDingHuoView2.as_view()), name="test"),
    url(r'^show_pic/(?P<order_list_id>\d+)$', staff_member_required(ShowPicView.as_view()), name="showpic"),
]
