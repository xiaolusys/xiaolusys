# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0025_orderlist_change_lack'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderGuarantee',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('desc', models.CharField(default=b'', max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='orderlist',
            name='press_num',
            field=models.IntegerField(default=0, verbose_name='\u50ac\u4fc3\u6b21\u6570'),
        ),
        migrations.AlterField(
            model_name='orderlist',
            name='stage',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u8fdb\u5ea6', choices=[(0, '\u8349\u7a3f'), (1, '\u5ba1\u6838'), (2, '\u4ed8\u6b3e'), (3, '\u6536\u8d27'), (4, '\u7ed3\u7b97'), (5, '\u5b8c\u6210'), (9, '\u5220\u9664')]),
        ),
        migrations.AddField(
            model_name='orderguarantee',
            name='purchase_order',
            field=models.ForeignKey(related_name='guarantees', verbose_name='\u8ba2\u8d27\u5355', to='dinghuo.OrderList'),
        ),
    ]
