# coding=utf-8


RECEIPT_OTHER = 0
RECEIPT_RETURN = 1
RECEIPT_BUYER = 2


def receipt_type_choice():
    return (
        (RECEIPT_OTHER, u'其他'),
        (RECEIPT_RETURN, u'用户退货'),
        (RECEIPT_BUYER, u'采购订货')
    )

WARE_NONE = 0
WARE_SH = 1
WARE_GZ = 2
WARE_COMPANY = 3
WARE_FCSZ = 4
WARE_FCGZ = 5
WARE_THIRD = 9
WARE_FCSLYC = 10
WARE_CHOICES = (
    (WARE_NONE, u'未选仓'),
    (WARE_SH, u'上海仓'),
    (WARE_GZ, u'广州仓'),
    (WARE_COMPANY, u'公司仓'),
    (WARE_FCSZ, u'蜂巢苏州仓'),
    (WARE_FCGZ, u'蜂巢广州仓'),
    (WARE_THIRD, u'第三方仓'),
    (WARE_FCSLYC, u'蜂巢十里洋场'),
)

SOURCE_JIMEI    = u'jimei'
SOURCE_FENGCHAO = u'fengchao'
SOURCE_YOUHE    = u'youhe'
SOURCE_CHOICES = (
    (SOURCE_JIMEI, u'己美'),
    (SOURCE_FENGCHAO, u'蜂巢'),
    (SOURCE_YOUHE, u'优禾'),
)

CAN_MERGE_ORDER_WHS_IDS = (1,2,3,4,5,10)