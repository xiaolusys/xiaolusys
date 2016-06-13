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
