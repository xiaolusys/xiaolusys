# coding=utf-8
class PSI_STATUS:
    PAID = 'paid'
    PREPARE_BOOK = 'prepare_book'
    BOOKED = 'booked'
    READY = 'ready'
    THIRD_SEND = 'third_send'
    ASSIGNED = 'assigned'
    MERGED = 'merged'
    WAITSCAN = 'waitscan'
    WAITPOST = 'waitpost'
    SENT = 'sent'
    FINISH = 'finish'
    CANCEL = 'cancel'
    HOLDING = 'holding'
    CHOICES = (
        ('paid', u'刚付待处理'),
        ('prepare_book', u'待订货'),
        ('booked', u'待备货'),
        ('ready', u'待分配'),
        ('third_send', u'待第三方发货'),
        ('assigned', u'待合单'),
        ('merged', u'待打单'),
        ('waitscan', u'待扫描'),
        ('waitpost', u'待称重'),
        ('sent', u'待收货'),
        ('finish', u'完成'),
        ('cancel', u'取消'),
        ('holding', u'挂起'),
    )
IN_EFFECT = "IN_EFFECT"
INVALID_STATUS = 'INVALID'
SYS_ORDER_STATUS = (
    (IN_EFFECT, u'有效'),
    (INVALID_STATUS, u'无效'),
)


class PO_STATUS:
    PKG_NEW_CREATED = 'PKG_NEW_CREATED'
    WAIT_PREPARE_SEND_STATUS = 'WAIT_PREPARE_SEND_STATUS'
    WAIT_CHECK_BARCODE_STATUS = 'WAIT_CHECK_BARCODE_STATUS'
    WAIT_SCAN_WEIGHT_STATUS = 'WAIT_SCAN_WEIGHT_STATUS'
    WAIT_CUSTOMER_RECEIVE = 'WAIT_CUSTOMER_RECEIVE'
    FINISHED_STATUS = 'FINISHED_STATUS'
    DELETE = 'DELETE'
    CHOICES = (
        (PKG_NEW_CREATED, u'初始状态'),
        (WAIT_PREPARE_SEND_STATUS, u'待发货准备'),
        (WAIT_CHECK_BARCODE_STATUS, u'待扫描验货'),
        (WAIT_SCAN_WEIGHT_STATUS, u'待扫描称重'),
        (WAIT_CUSTOMER_RECEIVE, u'待收货'),
        (FINISHED_STATUS, u'已到货'),
        (DELETE, u'已作废')
    )