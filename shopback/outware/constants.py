# coding: utf8
from __future__ import absolute_import, unicode_literals

GOOD = 1
ERROR = 2

NORMAL  = 1
RECEIVED = 2
LACKGOODS = 3
ARRIVED = 4
PACKING = 50
LOADING = 65
SENDED  = 80
CANCEL  = 100

SKU_TYPE_PRODUCT = {'code': 10, 'name': '普通商品'}
SKU_TYPE_GIFTS   = {'code': 20, 'name': '赠品'}
SKU_TYPE_METARIAL = {'code': 30, 'name': '包材'}

ORDER_TYPE_USUAL = {'code': 10, 'name': '普通订单'}
ORDER_TYPE_CROSSBOADER = {'code': 40, 'name': '跨境订单'}
ORDER_TYPE_BOOKING = {'code': 50, 'name': '预售订单'}

DECLARE_TYPE_NONE   = {'code': 0, 'name': '无需报关'}
DECLARE_TYPE_BOUND  = {'code': 10, 'name': '保税仓'}
DECLARE_TYPE_DIRECT  = {'code': 20, 'name': '直邮'}

ORDER_RETURN   = {'code': 301, 'name': '退仓单'}
ORDER_SALE     = {'code': 401, 'name': '销售订单'}
ORDER_REFUND   = {'code': 501, 'name': '销退货单'}
ORDER_PURCHASE = {'code': 601, 'name': '采购入仓单'}
ORDER_LACKGOOD = {'code': 10001, 'name': '订单缺货单'}

ACTION_SUPPLIER_CREATE = {'code': 40, 'name': '创建供应商'}

ACTION_SKU_CREATE = {'code': 30, 'name': '创建商品SKU信息'}
ACTION_SKU_EDIT  = {'code': 31,  'name': '修改商品SKU信息'}
ACTION_UNION_SKU_AND_SUPPLIER  = {'code': 45, 'name': '商品SKU供应商品关联'}
ACTION_SKU_STOCK_PULL = {'code': 65, 'name': 'SKU库存拉取'}


ACTION_PO_CREATE = {'code': 10, 'name': '创建入仓单'}
ACTION_PO_CANCEL = {'code': 11, 'name': '取消入仓单'}
ACTION_PO_RETURN = {'code': 55, 'name': '创建退仓单'}

ACTION_ORDER_CREATE = {'code': 20, 'name': '推送订单'}
ACTION_ORDER_CANCEL = {'code': 21, 'name': '取消订单'}
ACTION_ORDER_REFUND = {'code': 23, 'name': '创建销退单'}

ACTION_ORDER_SEND_FEEDBACK   = {'code': 1001, 'name': '订单发货回调'}
ACTION_ORDER_STATE_FEEDBACK  = {'code': 1002, 'name': '订单状态变更回调'}
ACTION_ORDER_RETURN_FEEDBACK = {'code': 1003, 'name': '销退入库回调'}
ACTION_ORDER_GOODLACK_FEEDBACK  = {'code': 1004, 'name': '订单缺货回调'}
ACTION_PO_CREATE_FEEDBACK = {'code': 1005, 'name': '入仓确认回调'}
ACTION_PO_RETURN_FEEDBACK = {'code': 1006, 'name': '退仓出库回调'}

ATION_ORDER_CHANNEL_CREATE   = {'code': 150, 'name': '销售渠道创建'}

ACTION_CROSSORDER_CREATE = {'code': 170, 'name': '跨境推送订单'}
# ACTION_CROSSSKU_CREATE   = {'code': 180, 'name': '创建跨境商品SKU信息'}
# ACTION_CROSSSKU_EDIT     = {'code': 185, 'name': '跨境推送订单'}
# ACTION_CROSSDECLARE_CREATE = {'code': 187, 'name': '口岸备案备案信息推送'}
ACTION_CROSSPO_CREATE      = {'code': 195, 'name': '创建跨境采购单'}

ACTION_LIST = [
    ACTION_SKU_CREATE,
    ACTION_SKU_EDIT,
    ACTION_UNION_SKU_AND_SUPPLIER,
    ACTION_SKU_STOCK_PULL,
    ACTION_SUPPLIER_CREATE,
    ACTION_PO_CREATE,
    ACTION_PO_CANCEL,
    ACTION_PO_RETURN,
    ACTION_PO_CREATE_FEEDBACK,
    ACTION_PO_RETURN_FEEDBACK,
    ACTION_ORDER_CREATE,
    ACTION_ORDER_CANCEL,
    ACTION_ORDER_REFUND,
    ACTION_ORDER_SEND_FEEDBACK,
    ACTION_ORDER_STATE_FEEDBACK,
    ACTION_ORDER_RETURN_FEEDBACK,
    ACTION_ORDER_GOODLACK_FEEDBACK,
    ATION_ORDER_CHANNEL_CREATE,
    ACTION_CROSSORDER_CREATE,
    ACTION_CROSSPO_CREATE
]








