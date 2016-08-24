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
WARE_THIRD = 9
WARE_CHOICES = ((WARE_NONE, u'未选仓'),
                (WARE_SH, u'上海仓'),
                (WARE_GZ, u'广州仓'),
                (WARE_COMPANY, u'公司仓'),
                (WARE_THIRD, u'第三方仓'),)