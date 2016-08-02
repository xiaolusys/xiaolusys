# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from flashsale.pay.models.user import Customer


def update_first_paytime(apps, schema_editor):
    SaleTrade = apps.get_model('pay', 'SaleTrade')

    for customer in Customer.objects.all():
        trade = SaleTrade.objects.filter(buyer_id=customer.id, pay_time__isnull=False).order_by('pay_time').first()
        if trade:
            customer.first_paytime = trade.pay_time
            customer.save()


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0028_add_price_to_flashsale_favorites'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='first_paytime',
            field=models.DateTimeField(null=True, verbose_name='\u9996\u6b21\u8d2d\u4e70\u65e5\u671f', blank=True),
        ),
        migrations.RunPython(update_first_paytime),
    ]
