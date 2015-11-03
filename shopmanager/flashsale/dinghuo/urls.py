# coding:utf-8
from django.conf.urls import include, url
from flashsale.dinghuo import views
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .views import DailyDingHuoStatsView, StatsByProductIdView, DailyWorkView
from django.views.decorators.csrf import csrf_exempt
from .views_change_detail import ChangeDetailView, AutoNewOrder, change_inferior_num
from .views_data_stats import DailyStatsView, StatsProductView, StatsSupplierView, StatsDinghuoView
from .view_daily_work import DailyDingHuoView, DailyDingHuoView2, ShowPicView, DailyDingHuoOptimizeView
from .point_every_day import RecordPointView
from .views_sale_status import EntranceView, SaleHotView, TopStockView, SaleBadView
from .view_refund_supplier import StatisRefundSupView, change_duihuo_status
import views_wuliu
import views_sale_status
import views_product
urlpatterns = [

    url(r'^searchproduct/$', views.search_product, name='searchProduct'),                       #搜索所有的商品 ajax
    url(r'^initdraft/$', views.init_draft, name='init_draft'),                                  #初始化草稿箱
    url(r'^dingdan/$', staff_member_required(views.new_order), name="new_order"),               #订单页面填写完成后跳转
    url(r'^delcaogao/$', views.del_draft, name="delcaogao"),                                    #删除所有草稿
    url(r'^data-chart/$', views.data_chart, name="data-chart"),
    url(r'^adddetail/(?P<outer_id>\d+)$', views.add_purchase, name="adddetail"),
    url(r'^plusquantity/$', views.plus_quantity, name="plusquantity"),                          #增加草稿里面的一个商品的数量
    url(r'^plusordertail/$', views.plusordertail, name="plusordertail"),                        #增加订单详情里面的一个商品的数量
    url(r'^minusordertail/$', views.minusordertail, name="minusordertail"),                     #减少订单详情里面的一个商品的数量
    url(r'^minusarrivedquantity/$', views.minusarrived, name="minusarrivedquantity"),           #减少
    url(r'^minusquantity/$', views.minusquantity, name="minusquantity"),                        #减少草稿里面的一个商品的数量
    url(r'^removedraft/$', views.removedraft, name="removedraft"),                              #删除草稿里面的一个商品
    url(r'^detail/(?P<orderdetail_id>\d+)/$', views.viewdetail, name="mydetail"),
    url(r'^wuliu/(?P<orderdetail_id>\d+)/$', views_wuliu.view_wuliu, name="wuliu"),
    url(r'^detaillayer/(?P<orderdetail_id>\d+)/$', views.detaillayer, name="detaillayer"),
    url(r'^changestatus/$', views.changestatus, name="changestatus"),
    url(r'^changedetail/(?P<order_detail_id>\d+)/$',csrf_exempt(staff_member_required(ChangeDetailView.as_view())), name="changedetail"),
    url(r'^daily/', staff_member_required(DailyDingHuoStatsView.as_view()), name="daily_ding_huo_stats"),  #大货每天统计
    url(r'^changearrivalquantity/$', views.changearrivalquantity, name="changearrivalquantity"),
    url(r'^statsbypid/(?P<product_id>\d+)/$', staff_member_required(StatsByProductIdView.as_view()), name="statsbypid"),  #根据商品id统计大货
    url(r'^dailywork/', staff_member_required(DailyWorkView.as_view()), name="dailywork"),      #爆款
    url(r'^setusertogroup/$', views.setusertogroup, name="setusertogroup"),                     #分配用户到组
    url(r'^adddetailtodinghuo/$', views.add_detail_to_ding_huo, name="add_detail_to_ding_huo"), #增加订货详情
    url(r'^changeorderlist/$', views.modify_order_list, name="modify_order_list"),
    url(r'^auto_new_order/(?P<order_list_id>\d+)/$', AutoNewOrder.as_view(), name="auto_new_order"),
    url(r'^change_inferior_num/$', change_inferior_num, name="change_inferior_num"),
    url(r'^daily_stats/(?P<prev_day>\d+)/$', staff_member_required(DailyStatsView.as_view()), name="daily_stats"),
    url(r'^daily_work/$', staff_member_required(DailyDingHuoView.as_view()), name="dailywork2"),
    url(r'^stats_product/$', staff_member_required(StatsProductView.as_view()), name="stats_product"),
    url(r'^stats_supplier/$', staff_member_required(StatsSupplierView.as_view()), name="stats_supplier"),
    url(r'^point_every_day/$', csrf_exempt(staff_member_required(RecordPointView.as_view())), name="point_every_day"),
    url(r'^begin_ding_huo/$', staff_member_required(DailyDingHuoView2.as_view()), name="begin_to_ding"),
    url(r'^begin_ding_huo_optimize/$', staff_member_required(DailyDingHuoOptimizeView.as_view()), name="ding2"),
    url(r'^show_pic/(?P<order_list_id>\d+)$', staff_member_required(ShowPicView.as_view()), name="showpic"),
    url(r'^sale_status/$', staff_member_required(EntranceView.as_view()), name="sale_status"),
    url(r'^sale_hot/$', staff_member_required(SaleHotView.as_view()), name="sale_hot"),          #热销的商品
    url(r'^sale_bad/$', staff_member_required(SaleBadView.as_view()), name="sale_bad"),          #滞销的商品
    url(r'^top_stock/$', staff_member_required(TopStockView.as_view()), name="top_stock"),          #库存最多的
    url(r'^daystats_ding_huo/$', StatsDinghuoView.as_view(), name="start_ding_huo"),      #每日订货统计
    url(r'^tuihuo/$', StatisRefundSupView.as_view(), name="tuihuo"),      # 退货统计　
    url(r'^tuihuo/change_status/$', staff_member_required(change_duihuo_status), name="change_tuihuo_status"), # 退货状态修改　
    url(r'^change_kucun/$', staff_member_required(views_sale_status.ChangeKunView.as_view()), name="change_kucun"), #修改上架前库存
    url(r'^sale_warning/$', staff_member_required(views_sale_status.SaleStatusView.as_view()), name="sale_warning"), #销售预警
    url(r'^set_remain_num/$', staff_member_required(views_product.SetRemainNumView.as_view()), name="set_remian"), #设置预留数
]
