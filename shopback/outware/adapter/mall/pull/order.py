# coding: utf8
from __future__ import absolute_import, unicode_literals

from flashsale.pay.models import SaleTrade, SaleOrder, SaleRefund
from ....models import OutwareOrder, OutwareOrderSku
from shopback.outware import constants
from shopback.items.models import ProductSku
from shopback.logistics.models import LogisticsCompany
from shopback.dinghuo.models import InBound, InBoundDetail


def update_saletrade_by_outware_packages(order_code, dict_obj):
    """
    order_code: xd16111358284ace3a74f
    dict_obj:  {
          "packages": [
            {
              "package_items": [
                {
                  "sku_qty": 2,
                  "object": "OutwarePackageSku",
                  "sku_code": "SP111111AA",
                  "batch_no": "AJEV"
                }
              ],
              "object": "OutwarePackage",
              "carrier_code": "YUNDA",
              "logistics_no": "9867542222",
              "store_code": "SZWH01"
            }
          ],
          "order_type": 401,
          "order_code": "xd16111358284ace3a74f",
          "object": "OutwareObject"
        }
    """
    # TODO@MENTION ,该方法未被使用，实现逻辑查看OutwarePackage.create_by_push_info
    out_sid = order_code['dict_obj']['packages'][0]['logistics_no']
    logistics_company = LogisticsCompany.get_by_fengchao_code(order_code['dict_obj']['carrier_code'])# order_code['dict_obj']['carrier_code']
    sku_dict = {}
    for line in order_code['dict_obj']['packages']:
        sku = ProductSku.get_by_outer_id(line['store_code'])

    outware_order = OutwareOrder.objects.filter(union_order_code=order_code).first()
    outware_order.get_package.finish_third_package(out_sid, logistics_company)
    outware_order.change_order_status(constants.SENDED)


def update_refundproduct_by_outware_inbound(order_code, dict_obj):
    """
    order_code: fid201702055896d6ecf0f66
    dict_obj:{
          "object": "OutwareInboundOrder",
          "inbound_skus": [
            {
              "object": "OutwareInboundSku",
              "pull_bad_qty": 1,
              "sku_code": "SP111111AA",
              "batch_no": "AJEV",
              "pull_good_qty": 2
            }
          ],
          "order_type": 501,
          "order_code": "fid201702055896d6ecf0f66",
          "store_code": "SZWH01"
        }
    """
    # inbound_skus =
    # orderlist_id =
    # express_no =
    # relate_orderids =
    # supplier_id =
    # user =
    inbound_sku = dict_obj.inbound_skus[0]
    s_refund = SaleRefund.objects.get(refund_no=order_code)
    # 如果申请退款数量与退货正品数量相等，则确认退货
    if s_refund.refund_num == inbound_sku.pull_good_qty:
        s_refund.refund_confirm()
    else:
        feedback = '仓库确认入仓正品{0}件，次品{1}件,与退款申请数{2}件有差异，不能自动确认退款，请联系在线客服,谢谢!'
        feedback = feedback.format([inbound_sku.pull_good_qty, inbound_sku.pull_bad_qty, s_refund.refund_num])
        s_refund.refund_refuse(feedback)


def update_outware_order_by_goodlack_notify(order_code, dict_obj):
    """
    order_code: xd16111358284ace3a74f
    dict_obj: {
          "object": "OutWareLackOrder",
          "order_code": "xd16111358284ace3a74f",
          "order_type": 701,
          "lack_goods": [
            {
              "lack_qty": 2,
              "sku_name": "ABCD",
              "sku_code": "SP11111AAA",
              "object": "OutWareLackOrderGood"
            }
          ]
        }
    """
    # TODO@MERON.2017.4.25
    # raise Exception('订单商品缺货请实现: order_code=%s'% order_code)