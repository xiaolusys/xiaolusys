# coding=utf-8
from django.conf.urls import include, url

from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from rest_framework import routers, viewsets

from django.views.decorators.csrf import csrf_exempt
from . import views
from .views import view_supplier_sku

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'pending_dinghuo', views.PendingDingHuoViewSet)
router.register(r'instant_dinghuo', views.InstantDingHuoViewSet, 'dinghuo')
router.register(r'dinghuo_orderlist', views.DingHuoOrderListViewSet, 'dinghuo_orderlist')
router.register(r'repurchase', views.RePurchaseViewSet, 'repurchase')
router.register(r'purchase_return', views.ReturnGoodsViewSet, 'purchase_return')
router.register(r'inbound', views.InBoundViewSet, 'inbound')

urlpatterns = [
    url(r'^searchproduct/$', views.search_product,
        name='searchProduct'),  # 搜索所有的商品 ajax
    url(r'^initdraft/$',
        views.init_draft,
        name='init_draft'),  # 初始化草稿箱
    url(r'^dingdan/$',
        staff_member_required(views.new_order),
        name="new_order"),  # 订单页面填写完成后跳转
    url(r'^delcaogao/$',
        views.del_draft,
        name="delcaogao"),  # 删除所有草稿
    url(r'^data-chart/$',
        views.data_chart,
        name="data-chart"),
    url(r'^adddetail/(?P<outer_id>\d+)$',
        views.add_purchase,
        name="adddetail"),
    url(r'^plusquantity/$',
        views.plus_quantity,
        name="plusquantity"),  # 增加草稿里面的一个商品的数量
    url(r'^plusordertail/$',
        views.plusordertail,
        name="plusordertail"),  # 增加订单详情里面的一个商品的数量
    url(r'^minusordertail/$',
        views.minusordertail,
        name="minusordertail"),  # 减少订单详情里面的一个商品的数量
    url(r'^minusarrivedquantity/$',
        views.minusarrived,
        name="minusarrivedquantity"),  # 减少
    url(r'^minusquantity/$',
        views.minusquantity,
        name="minusquantity"),  # 减少草稿里面的一个商品的数量
    url(r'^removedraft/$',
        views.removedraft,
        name="removedraft"),  # 删除草稿里面的一个商品
    url(r'^detail/(?P<orderdetail_id>\d+)/$',
        views.viewdetail,
        name="mydetail"),
    url(r'^wuliu/(?P<orderdetail_id>\d+)/$',
        views.view_wuliu,
        name="wuliu"),
    url(r'^detaillayer/(?P<orderdetail_id>\d+)/$',
        views.detaillayer,
        name="detaillayer"),
    url(r'^changestatus/$',
        views.changestatus,
        name="changestatus"),
    url(r'^changedetail/(?P<order_detail_id>\d+)/$',
        csrf_exempt(staff_member_required(views.ChangeDetailView.as_view())),
        name="changedetail"),
    url(r'^changedetail/(?P<order_detail_id>\d+)/export/$',
        csrf_exempt(staff_member_required(views.ChangeDetailExportView.as_view())),
        name="changedetail_export"),
    url(r'^changedetail/(?P<order_detail_id>\d+)/package_export/$',
        csrf_exempt(staff_member_required(views.ChangeDetailExportView.as_view())),
        name="changedetail_export"),
    url(r'^changedetail/export/$',
        csrf_exempt(staff_member_required(views.DinghuoStatsExportView.as_view())),
        name="changedetails_export"),
    url(r'^daily/',
        staff_member_required(views.DailyDingHuoStatsView.as_view()),
        name="daily_ding_huo_stats"),  # 大货每天统计
    url(r'^changearrivalquantity/$',
        views.changearrivalquantity,
        name="changearrivalquantity"),
    url(r'^change_inbound_quantity/$',
        views.change_inbound_quantity,
        name="change_inbound_quantity"),
    url(r'^statsbypid/(?P<product_id>\d+)/$',
        staff_member_required(views.StatsByProductIdView.as_view()),
        name="statsbypid"),
    # 根据商品id统计大货
    url(r'^dailywork/',
        staff_member_required(views.DailyWorkView.as_view()),
        name="dailywork"),  # 爆款
    url(r'^setusertogroup/$',
        views.setusertogroup,
        name="setusertogroup"),  # 分配用户到组
    url(r'^adddetailtodinghuo/$',
        views.add_detail_to_ding_huo,
        name="add_detail_to_ding_huo"),  # 增加订货详情
    url(r'^changeorderlist/$',
        views.modify_order_list,
        name="modify_order_list"),
    url(r'^auto_new_order/(?P<order_list_id>\d+)/$',
        views.AutoNewOrder.as_view(),
        name="auto_new_order"),
    url(r'^change_inferior_num/$',
        views.change_inferior_num,
        name="change_inferior_num"),
    url(r'^daily_stats/(?P<prev_day>\d+)/$',
        staff_member_required(views.DailyStatsView.as_view()),
        name="daily_stats"),
    url(r'^daily_work/$',
        staff_member_required(views.DailyDingHuoView.as_view()),
        name="dailywork2"),
    url(r'^stats_product/$',
        staff_member_required(views.StatsProductView.as_view()),
        name="stats_product"),
    url(r'^stats_supplier/$',
        staff_member_required(views.StatsSupplierView.as_view()),
        name="stats_supplier"),
    url(r'^point_every_day/$',
        csrf_exempt(staff_member_required(views.RecordPointView.as_view())),
        name="point_every_day"),
    url(r'^begin_ding_huo/$',
        staff_member_required(views.DailyDingHuoView2.as_view()),
        name="begin_to_ding"),
    url(r'^begin_ding_huo_optimize/$',
        staff_member_required(views.DailyDingHuoOptimizeView.as_view()),
        name="ding2"),
    url(r'^show_pic/(?P<order_list_id>\d+)$',
        staff_member_required(views.ShowPicView.as_view()),
        name="showpic"),
    url(r'^sale_status/$',
        staff_member_required(views.EntranceView.as_view()),
        name="sale_status"),
    url(r'^sale_hot/$',
        staff_member_required(views.SaleHotView.as_view()),
        name="sale_hot"),  # 热销的商品
    url(r'^sale_bad/$',
        staff_member_required(views.SaleBadView.as_view()),
        name="sale_bad"),  # 滞销的商品
    url(r'^top_stock/$',
        staff_member_required(views.TopStockView.as_view()),
        name="top_stock"),  # 库存最多的
    url(r'^daystats_ding_huo/$',
        views.StatsDinghuoView.as_view(),
        name="start_ding_huo"),  # 每日订货统计
    url(r'^tuihuo/$',
        views.StatisRefundSupView.as_view(),
        name="tuihuo"),  # 退货统计　
    url(r'^tuihuo/change_status/$',
        staff_member_required(views.change_duihuo_status),
        name="change_tuihuo_status"),
    url(r'^returngoods/update_memo/$',
        staff_member_required(views.change_return_goods_memo),
        name="update_memo"),
    url(r'^returngoods/modify_return_goods_sku/$',
        staff_member_required(views.modify_return_goods_sku),
        name="modify_return_goods_sku"),
    url(r'^returngoods/delete_return_goods_sku/$',
        staff_member_required(views.delete_return_goods_sku),
        name="delete_return_goods_sku"),
    url(r'^returngoods/set_return_goods_sku_send/$',
        staff_member_required(views.set_return_goods_sku_send),
        name="set_return_goods_sku_send"),
    url(r'^returngoods/set_transactor/$',
        staff_member_required(views.set_transactor),
        name="set_transactor"),
    url(r'^returngoods/export/$',
        staff_member_required(views.export_return_goods),
        name="export_return_goods"),
    url(r'^returngoods/mark_unreturn/$',
        staff_member_required(views.mark_unreturn),
        name='mark_unreturn'),
    url(r'^returngoods/deal/$',
        staff_member_required(views.returngoods_deal),
        name='returngoods_deal'),
    url(r'^returngoods/add_sku/$',
        staff_member_required(views.returngoods_add_sku),
        name='returngoods_add_sku'),

    # 退货状态修改　
    url(r'^tuihuo/change_sum_amount/$',
        staff_member_required(views.change_sum_price),
        name="change_tuihuo_amount"),  # 退货金额修改
    url(r'^change_kucun/$',
        staff_member_required(views.views_sale_status.ChangeKunView.as_view()),
        name="change_kucun"),
    # 修改上架前库存
    url(r'^sale_warning/$',
        staff_member_required(views.views_sale_status.SaleStatusView.as_view()),
        name="sale_warning"),
    # 销售预警
    url(r'^set_remain_num/$',
        staff_member_required(views.views_product.SetRemainNumView.as_view()),
        name="set_remian"),
    # 设置预留数
    url(r'^product_category/$',
        staff_member_required(views.ProductCategoryAPIView.as_view()),
        name="product_category"),
    # 商品分类api
    url(r'^skuapi/$',
        staff_member_required(views.SkuAPIView.as_view()),
        name="product_category"),  # 商品分类api
    url(r'^stats/$',
        staff_member_required(views.views_line_show.InventoryDataLineShow.as_view()),
        name="line_show"),
    # 折线图显示数据
    url(r'^add_ding_huo/$',
        staff_member_required(views.AddDingHuoView.as_view()),
        name="add_ding_huo"),
    # update订货单部分信息
    url(r'^update_dinghuo/$', views.update_dinghuo_part_information, name="update_dinghuo_part_information"),
    # 生成退货单
    url(r'^generate_return_goods/$', views.generate_return_goods, name="generate_return_goods"),
    url(r'^tuihuo/set_return_goods_failed/$', views.set_return_goods_failed, name="set_return_goods_failed"),
    url(r'^supplier_sku/(?P<salesupplier_id>\d+)$',
        view_supplier_sku.get_supplier_sku,
        name="get_supplier_sku"),
    url(r'^supplier_sku/(?P<salesupplier_id>\d+)/excel/$',
        view_supplier_sku.get_supplier_sku_excel,
        name="get_supplier_sku_excel"),

]

urlpatterns += router.urls
