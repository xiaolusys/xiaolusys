# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import flashsale.pay.models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0019_add_field_salecategory_cid'),
        ('pay', '0023_change_refund_proofpic_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelproduct',
            name='extras',
            field=models.CharField(default=flashsale.pay.models.default_modelproduct_extras_tpl, max_length=5000, verbose_name='\u9644\u52a0\u4fe1\u606f'),
        ),
        migrations.AddField(
            model_name='modelproduct',
            name='salecategory',
            field=models.ForeignKey(related_name='model_product_set', default=None, verbose_name='\u5206\u7c7b', to='supplier.SaleCategory', null=True),
        ),
        migrations.AlterField(
            model_name='district',
            name='grade',
            field=models.IntegerField(default=0, verbose_name='\u7b49\u7ea7', choices=[(1, '\u7701'), (2, '\u5e02'), (3, '\u533a/\u53bf'), (4, '\u8857\u9053')]),
        ),
        migrations.AlterField(
            model_name='productdetail',
            name='is_sale',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u4e13\u573a'),
        ),
        migrations.AlterField(
            model_name='productdetail',
            name='is_seckill',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u79d2\u6740'),
        ),
        migrations.AlterUniqueTogether(
            name='modelproduct',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='modelproduct',
            name='buy_limit',
        ),
        migrations.RemoveField(
            model_name='modelproduct',
            name='per_limit',
        ),
    ]
