# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('supplier', '0004_saleproduct_orderlist_show_memo'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('type', models.IntegerField(verbose_name='\u8d26\u5355\u7c7b\u578b', choices=[(-1, '\u4ed8\u6b3e'), (0, '\u4f5c\u5e9f'), (1, '\u6536\u6b3e')])),
                ('status', models.IntegerField(verbose_name='\u8d26\u5355\u72b6\u6001', choices=[(0, '\u5f85\u5904\u7406'), (1, '\u5df2\u5904\u7406'), (2, '\u5df2\u5b8c\u6210')])),
                ('bill_method', models.IntegerField(default=11, verbose_name='\u4ed8\u6b3e\u7c7b\u578b', choices=[(11, '\u8d27\u5230\u4ed8\u6b3e'), (12, '\u9884\u4ed8\u6b3e'), (13, '\u4ed8\u6b3e\u63d0\u8d27'), (14, '\u5176\u5b83')])),
                ('plan_amount', models.FloatField(verbose_name='\u8ba1\u5212\u6b3e\u989d')),
                ('amount', models.FloatField(default=0, verbose_name='\u5b9e\u6536\u6b3e\u989d')),
                ('pay_method', models.IntegerField(verbose_name='\u652f\u4ed8\u65b9\u5f0f', choices=[(1, '\u6dd8\u5b9d\u4ee3\u4ed8'), (2, '\u8f6c\u6b3e'), (3, '\u81ea\u4ed8'), (4, '\u76f4\u9000'), (5, '\u4f59\u989d\u62b5\u6263')])),
                ('pay_taobao_link', models.TextField(null=True, verbose_name='\u6dd8\u5b9d\u94fe\u63a5')),
                ('receive_account', models.CharField(max_length=50, null=True, verbose_name='\u6536\u6b3e\u8d26\u53f7')),
                ('receive_name', models.CharField(max_length=16, null=True, verbose_name='\u6536\u6b3e\u8d26\u53f7')),
                ('pay_account', models.TextField(null=True, verbose_name='\u4ed8\u6b3e\u8d26\u53f7')),
                ('transcation_no', models.CharField(max_length=100, null=True, verbose_name='\u4ea4\u6613\u5355\u53f7')),
                ('attachment', models.FileField(upload_to=b'', null=True, verbose_name='\u9644\u4ef6')),
                ('delete_reason', models.CharField(max_length=100, null=True, verbose_name='\u4f5c\u5e9f\u7406\u7531')),
                ('note', models.CharField(max_length=100, verbose_name='\u5907\u6ce8')),
                ('creater', models.ForeignKey(verbose_name='\u521b\u5efa\u4eba', to=settings.AUTH_USER_MODEL)),
                ('supplier', models.ForeignKey(verbose_name='\u4f9b\u5e94\u5546', to='supplier.SaleSupplier', null=True)),
            ],
            options={
                'db_table': 'finance_bill',
                'verbose_name': '\u8d26\u5355\u8bb0\u5f55',
                'verbose_name_plural': '\u8d26\u5355\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='BillRelation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('object_id', models.TextField(null=True, verbose_name='\u5bf9\u8c61id', blank=True)),
                ('type', models.IntegerField(choices=[(1, '\u8ba2\u8d27\u4ed8\u6b3e'), (2, '\u8ba2\u8d27\u56de\u6b3e'), (3, '\u9000\u8d27\u6536\u6b3e')])),
                ('bill', models.ForeignKey(to='finance.Bill')),
                ('content_type', models.ForeignKey(verbose_name='\u5bf9\u8c61\u7c7b\u578b', blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'db_table': 'finance_billrelation',
                'verbose_name': '\u8d26\u5355\u8bb0\u5f55\u5173\u8054',
                'verbose_name_plural': '\u8d26\u5355\u8bb0\u5f55\u5173\u8054\u5217\u8868',
            },
        ),
    ]
