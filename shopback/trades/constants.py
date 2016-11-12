# coding=utf-8
class PSI_STATUS:
    PAID = 'paid'
    PREPARE_BOOK = 'prepare_book'
    BOOKED = 'booked'
    READY = 'ready'
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