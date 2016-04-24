# -*- coding:utf8 -*-
import datetime
from django.db import models
from common.utils import parse_datetime


class ItemNotify(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.BigIntegerField()
    num_iid = models.BigIntegerField()

    title = models.CharField(max_length=64, blank=True)

    sku_id = models.BigIntegerField(null=True, blank=True)
    sku_num = models.IntegerField(null=True, default=0)
    status = models.CharField(max_length=32, blank=True)

    increment = models.IntegerField(null=True, default=0)
    nick = models.CharField(max_length=32, blank=True)
    num = models.IntegerField(null=True, default=0)

    changed_fields = models.CharField(max_length=256, blank=True)
    price = models.CharField(max_length=10, blank=True)
    modified = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'修改时间')

    is_exec = models.BooleanField(default=False)

    class Meta:
        db_table = 'shop_notify_item'
        unique_together = ("user_id", "num_iid", "sku_id", "status")
        app_label = 'notify'

    def __unicode__(self):
        return '<%d,%d,%s,%s>' % (self.user_id, self.num_iid, str(self.sku_id), self.status)

    @classmethod
    def save_and_post_notify(cls, item_dict):
        item_notify, state = cls.objects.get_or_create(
            user_id=item_dict['user_id'],
            num_iid=item_dict['num_iid'],
            sku_id=item_dict.get('sku_id', None),
            status=item_dict['status'],
        )
        item_modified = datetime.datetime.strptime(item_dict['modified'], '%Y-%m-%d %H:%M:%S')
        if state or not item_notify.modified or item_notify.modified < item_modified:
            for k, v in item_dict.iteritems():
                hasattr(item_notify, k) and setattr(item_notify, k, v)
            item_notify.save()

            from shopapp.notify.tasks import process_item_notify_task
            process_item_notify_task.delay(item_notify.id)


class TradeNotify(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.BigIntegerField()
    tid = models.BigIntegerField()
    oid = models.BigIntegerField()

    nick = models.CharField(max_length=64, blank=True)

    seller_nick = models.CharField(max_length=64, blank=True)
    buyer_nick = models.CharField(max_length=64, blank=True)

    payment = models.CharField(max_length=10, blank=True)
    type = models.CharField(max_length=32, blank=True)

    status = models.CharField(max_length=32, blank=True)

    trade_mark = models.CharField(max_length=256, blank=True)

    modified = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'修改时间')

    is_exec = models.BooleanField(default=False)

    class Meta:
        db_table = 'shop_notify_trade'
        unique_together = ("user_id", "tid", "oid", "status")
        app_label = 'notify'

    def __unicode__(self):
        return '<%d,%d,%d,%s>' % (self.user_id, self.tid, self.oid, self.status)

    @classmethod
    def save_and_post_notify(cls, trade_dict):
        trade_notify, state = cls.objects.get_or_create(
            user_id=trade_dict['user_id'],
            tid=trade_dict['tid'],
            oid=trade_dict['oid'],
            status=trade_dict['status'],
        )
        trade_modified = datetime.datetime.strptime(trade_dict['modified'], '%Y-%m-%d %H:%M:%S')
        if state or not trade_notify.modified or trade_notify.modified < trade_modified:
            for k, v in trade_dict.iteritems():
                hasattr(trade_notify, k) and setattr(trade_notify, k, v)
            trade_notify.save()

            from shopapp.notify.tasks import process_trade_notify_task
            process_trade_notify_task.delay(trade_notify.id)


class RefundNotify(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.BigIntegerField()
    tid = models.BigIntegerField()
    oid = models.BigIntegerField()
    rid = models.BigIntegerField()

    nick = models.CharField(max_length=64, blank=True)
    seller_nick = models.CharField(max_length=64, blank=True)
    buyer_nick = models.CharField(max_length=64, blank=True)

    refund_fee = models.CharField(max_length=10, blank=True)
    status = models.CharField(max_length=32, blank=True)

    modified = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'修改时间')
    is_exec = models.BooleanField(default=False)

    class Meta:
        db_table = 'shop_notify_refund'
        unique_together = ("user_id", "tid", "oid", "rid", "status")
        app_label = 'notify'

    def __unicode__(self):
        return '<%d,%d,%d,%d,%s>' % (self.user_id, self.tid, self.oid, self.rid, self.status)

    @classmethod
    def save_and_post_notify(cls, refund_dict):
        refund_notify, state = RefundNotify.objects.get_or_create(
            user_id=refund_dict['user_id'],
            tid=refund_dict['tid'],
            oid=refund_dict['oid'],
            rid=refund_dict['rid'],
            status=refund_dict['status'],
        )
        refund_modified = datetime.datetime.strptime(refund_dict['modified'], '%Y-%m-%d %H:%M:%S')
        if state or not refund_notify.modified or refund_notify.modified < refund_modified:
            for k, v in refund_dict.iteritems():
                hasattr(refund_notify, k) and setattr(refund_notify, k, v)
            refund_notify.save()

            from shopapp.notify.tasks import process_refund_notify_task
            process_refund_notify_task.delay(refund_notify.id)
