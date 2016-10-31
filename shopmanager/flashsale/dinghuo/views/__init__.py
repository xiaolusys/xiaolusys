from .views import *
from .view_inbound import InBoundViewSet
from .views_change_detail import ChangeDetailView, AutoNewOrder, change_inferior_num, \
    ChangeDetailExportView, DinghuoStatsExportView, update_dinghuo_part_information, generate_return_goods
from .views_data_stats import DailyStatsView, StatsProductView, StatsSupplierView, StatsDinghuoView
from .view_daily_work import (DailyDingHuoView, DailyDingHuoView2, ShowPicView,
                              DailyDingHuoOptimizeView, SkuAPIView,
                              AddDingHuoView, InstantDingHuoViewSet)
from .point_every_day import RecordPointView
from .views_sale_status import EntranceView, SaleHotView, TopStockView, SaleBadView
from .view_refund_supplier import (
    StatisRefundSupView, change_duihuo_status, change_sum_price,
    change_return_goods_memo, modify_return_goods_sku, delete_return_goods_sku,
    set_return_goods_sku_send, set_transactor, export_return_goods,
    mark_unreturn, returngoods_add_sku, set_return_goods_failed,
    returngoods_deal, ReturnGoodsViewSet)
from .views_wuliu import view_wuliu
from .views_sale_status import ChangeKunView, SaleStatusView
from .views_product import SetRemainNumView
from .views_line_show import InventoryDataLineShow
from .views_lackgood import LackGoodOrderViewSet
from .views_stats import PurchaseStatsApiView
from .repurchase import RePurchaseViewSet