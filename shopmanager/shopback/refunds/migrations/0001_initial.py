# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shopback.refunds.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PayRefNumRcord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_cal', models.DateField(unique=True, verbose_name='\u7ed3\u7b97\u65e5\u671f', db_index=True)),
                ('ref_num_out', models.IntegerField(default=0, verbose_name='24h\u5916\u672a\u53d1\u8d27\u7533\u8bf7\u6570')),
                ('ref_num_in', models.IntegerField(default=0, verbose_name='24h\u5185\u672a\u53d1\u8d27\u7533\u8bf7\u6570')),
                ('ref_sed_num', models.IntegerField(default=0, verbose_name='\u53d1\u8d27\u540e\u7533\u8bf7\u6570')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f')),
            ],
            options={
                'db_table': 'flashsale_pay_refund_num_record',
                'verbose_name': '\u7279\u5356/\u9000\u6b3e\u6570\u8bb0\u5f55\u8868',
                'verbose_name_plural': '\u7279\u5356/\u9000\u6b3e\u6570\u8bb0\u5f55\u8868',
            },
        ),
        migrations.CreateModel(
            name='PayRefundRate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_cal', models.DateField(unique=True, verbose_name='\u7ed3\u7b97\u65e5\u671f', db_index=True)),
                ('ref_num', models.IntegerField(default=0, verbose_name='\u9000\u6b3e\u5355\u6570')),
                ('pay_num', models.IntegerField(default=0, verbose_name='\u4ed8\u6b3e\u5355\u6570')),
                ('ref_rate', models.FloatField(default=0.0, verbose_name='\u9000\u6b3e\u7387')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f')),
            ],
            options={
                'db_table': 'flashsale_pay_refundrate',
                'verbose_name': '\u7279\u5356/\u9000\u6b3e\u7387\u8868',
                'verbose_name_plural': '\u7279\u5356/\u9000\u6b3e\u7387\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='ProRefunRcord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('product', models.IntegerField(unique=True, verbose_name='\u4ea7\u54c1id', db_index=True)),
                ('ref_num_out', models.IntegerField(default=0, verbose_name='24h\u5916\u672a\u53d1\u8d27\u7533\u8bf7\u6570')),
                ('ref_num_in', models.IntegerField(default=0, verbose_name='24h\u5185\u672a\u53d1\u8d27\u7533\u8bf7\u6570')),
                ('ref_sed_num', models.IntegerField(default=0, verbose_name='\u53d1\u8d27\u540e\u7533\u8bf7\u6570')),
                ('contactor', models.BigIntegerField(default=0, verbose_name='\u63a5\u6d3d\u4eba', db_index=True)),
                ('pro_model', models.BigIntegerField(default=0, verbose_name='\u4ea7\u54c1\u6b3e\u5f0fid', db_index=True)),
                ('sale_date', models.DateField(auto_now=True, verbose_name='\u4e0a\u67b6\u65f6\u95f4', db_index=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f')),
            ],
            options={
                'db_table': 'flashsale_pay_product_refund_record',
                'verbose_name': '\u7279\u5356/\u4ea7\u54c1\u9000\u6b3e\u6570\u8bb0\u5f55\u8868',
                'verbose_name_plural': '\u7279\u5356/\u4ea7\u54c1\u9000\u6b3e\u6570\u8bb0\u5f55\u8868',
                'permissions': [('browser_all_pro_duct_ref_lis', '\u6d4f\u89c8\u4e70\u624b\u6240\u6709\u4ea7\u54c1\u7684\u9000\u8d27\u72b6\u51b5\u8bb0\u5f55')],
            },
        ),
        migrations.CreateModel(
            name='Refund',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name=b'ID', primary_key=True)),
                ('refund_id', models.CharField(default=shopback.refunds.models.default_refund_id, max_length=32, verbose_name=b'\xe9\x80\x80\xe6\xac\xbe\xe5\x8d\x95ID')),
                ('tid', models.CharField(max_length=32, verbose_name=b'\xe4\xba\xa4\xe6\x98\x93ID', blank=True)),
                ('title', models.CharField(max_length=64, verbose_name=b'\xe5\x87\xba\xe5\x94\xae\xe6\xa0\x87\xe9\xa2\x98', blank=True)),
                ('num_iid', models.BigIntegerField(default=0, null=True, verbose_name=b'\xe5\x95\x86\xe5\x93\x81ID')),
                ('seller_id', models.CharField(max_length=64, verbose_name=b'\xe5\x8d\x96\xe5\xae\xb6ID', blank=True)),
                ('buyer_nick', models.CharField(db_index=True, max_length=64, verbose_name=b'\xe4\xb9\xb0\xe5\xae\xb6\xe6\x98\xb5\xe7\xa7\xb0', blank=True)),
                ('seller_nick', models.CharField(max_length=64, verbose_name=b'\xe5\x8d\x96\xe5\xae\xb6\xe6\x98\xb5\xe7\xa7\xb0', blank=True)),
                ('mobile', models.CharField(db_index=True, max_length=20, verbose_name=b'\xe6\x89\x8b\xe6\x9c\xba', blank=True)),
                ('phone', models.CharField(db_index=True, max_length=20, verbose_name=b'\xe5\x9b\xba\xe8\xaf\x9d', blank=True)),
                ('total_fee', models.CharField(max_length=10, verbose_name=b'\xe6\x80\xbb\xe8\xb4\xb9\xe7\x94\xa8', blank=True)),
                ('refund_fee', models.CharField(max_length=10, verbose_name=b'\xe9\x80\x80\xe6\xac\xbe\xe8\xb4\xb9\xe7\x94\xa8', blank=True)),
                ('payment', models.CharField(max_length=10, verbose_name=b'\xe5\xae\x9e\xe4\xbb\x98', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True, verbose_name=b'\xe5\x88\x9b\xe5\xbb\xba\xe6\x97\xa5\xe6\x9c\x9f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, null=True, verbose_name=b'\xe4\xbf\xae\xe6\x94\xb9\xe6\x97\xa5\xe6\x9c\x9f', db_index=True)),
                ('oid', models.CharField(db_index=True, max_length=32, verbose_name=b'\xe8\xae\xa2\xe5\x8d\x95ID', blank=True)),
                ('company_name', models.CharField(max_length=64, verbose_name=b'\xe5\xbf\xab\xe9\x80\x92\xe5\x85\xac\xe5\x8f\xb8', blank=True)),
                ('sid', models.CharField(db_index=True, max_length=64, verbose_name=b'\xe5\xbf\xab\xe9\x80\x92\xe5\x8d\x95\xe5\x8f\xb7', blank=True)),
                ('reason', models.TextField(max_length=200, verbose_name=b'\xe9\x80\x80\xe6\xac\xbe\xe5\x8e\x9f\xe5\x9b\xa0', blank=True)),
                ('desc', models.TextField(max_length=1000, verbose_name=b'\xe6\x8f\x8f\xe8\xbf\xb0', blank=True)),
                ('has_good_return', models.BooleanField(default=False, verbose_name=b'\xe6\x98\xaf\xe5\x90\xa6\xe9\x80\x80\xe8\xb4\xa7')),
                ('is_reissue', models.BooleanField(default=False, verbose_name=b'\xe5\xb7\xb2\xe5\xa4\x84\xe7\x90\x86')),
                ('good_status', models.CharField(blank=True, max_length=32, verbose_name=b'\xe9\x80\x80\xe8\xb4\xa7\xe5\x95\x86\xe5\x93\x81\xe7\x8a\xb6\xe6\x80\x81', choices=[(b'BUYER_NOT_RECEIVED', b'\xe4\xb9\xb0\xe5\xae\xb6\xe6\x9c\xaa\xe6\x94\xb6\xe5\x88\xb0\xe8\xb4\xa7'), (b'BUYER_RECEIVED', b'\xe4\xb9\xb0\xe5\xae\xb6\xe5\xb7\xb2\xe6\x94\xb6\xe5\x88\xb0\xe8\xb4\xa7'), (b'BUYER_RETURNED_GOODS', b'\xe4\xb9\xb0\xe5\xae\xb6\xe5\xb7\xb2\xe9\x80\x80\xe8\xb4\xa7')])),
                ('order_status', models.CharField(blank=True, max_length=32, verbose_name=b'\xe8\xae\xa2\xe5\x8d\x95\xe7\x8a\xb6\xe6\x80\x81', choices=[(b'TRADE_NO_CREATE_PAY', b'\xe6\xb2\xa1\xe6\x9c\x89\xe5\x88\x9b\xe5\xbb\xba\xe6\x94\xaf\xe4\xbb\x98\xe5\xae\x9d\xe4\xba\xa4\xe6\x98\x93'), (b'WAIT_BUYER_PAY', b'\xe7\xad\x89\xe5\xbe\x85\xe4\xb9\xb0\xe5\xae\xb6\xe4\xbb\x98\xe6\xac\xbe'), (b'WAIT_SELLER_SEND_GOODS', b'\xe7\xad\x89\xe5\xbe\x85\xe5\x8d\x96\xe5\xae\xb6\xe5\x8f\x91\xe8\xb4\xa7'), (b'WAIT_BUYER_CONFIRM_GOODS', b'\xe7\xad\x89\xe5\xbe\x85\xe4\xb9\xb0\xe5\xae\xb6\xe7\xa1\xae\xe8\xae\xa4\xe6\x94\xb6\xe8\xb4\xa7'), (b'TRADE_BUYER_SIGNED', b'\xe5\xb7\xb2\xe7\xad\xbe\xe6\x94\xb6,\xe8\xb4\xa7\xe5\x88\xb0\xe4\xbb\x98\xe6\xac\xbe\xe4\xb8\x93\xe7\x94\xa8'), (b'TRADE_FINISHED', b'\xe4\xba\xa4\xe6\x98\x93\xe6\x88\x90\xe5\x8a\x9f'), (b'TRADE_CLOSED', b'\xe9\x80\x80\xe6\xac\xbe\xe6\x88\x90\xe5\x8a\x9f\xe4\xba\xa4\xe6\x98\x93\xe8\x87\xaa\xe5\x8a\xa8\xe5\x85\xb3\xe9\x97\xad'), (b'TRADE_CLOSED_BY_TAOBAO', b'\xe4\xbb\x98\xe6\xac\xbe\xe5\x89\x8d\xe5\x85\xb3\xe9\x97\xad\xe4\xba\xa4\xe6\x98\x93')])),
                ('cs_status', models.IntegerField(default=1, verbose_name=b'\xe5\xae\xa2\xe6\x9c\x8d\xe4\xbb\x8b\xe5\x85\xa5\xe7\x8a\xb6\xe6\x80\x81', choices=[(1, b'\xe4\xb8\x8d\xe9\x9c\x80\xe5\xae\xa2\xe6\x9c\x8d\xe4\xbb\x8b\xe5\x85\xa5'), (2, b'\xe9\x9c\x80\xe8\xa6\x81\xe5\xae\xa2\xe6\x9c\x8d\xe4\xbb\x8b\xe5\x85\xa5'), (3, b'\xe5\xae\xa2\xe6\x9c\x8d\xe5\xb7\xb2\xe7\xbb\x8f\xe4\xbb\x8b\xe5\x85\xa5'), (4, b'\xe5\xae\xa2\xe6\x9c\x8d\xe5\x88\x9d\xe5\xae\xa1\xe5\xae\x8c\xe6\x88\x90'), (5, b'\xe5\xae\xa2\xe6\x9c\x8d\xe4\xb8\xbb\xe7\xae\xa1\xe5\xa4\x8d\xe5\xae\xa1\xe5\xa4\xb1\xe8\xb4\xa5'), (6, b'\xe5\xae\xa2\xe6\x9c\x8d\xe5\xa4\x84\xe7\x90\x86\xe5\xae\x8c\xe6\x88\x90')])),
                ('status', models.CharField(blank=True, max_length=32, verbose_name=b'\xe9\x80\x80\xe6\xac\xbe\xe7\x8a\xb6\xe6\x80\x81', choices=[(b'NO_REFUND', b'\xe6\xb2\xa1\xe6\x9c\x89\xe9\x80\x80\xe6\xac\xbe'), (b'WAIT_SELLER_AGREE', b'\xe4\xb9\xb0\xe5\xae\xb6\xe5\xb7\xb2\xe7\xbb\x8f\xe7\x94\xb3\xe8\xaf\xb7\xe9\x80\x80\xe6\xac\xbe'), (b'WAIT_BUYER_RETURN_GOODS', b'\xe5\x8d\x96\xe5\xae\xb6\xe5\xb7\xb2\xe7\xbb\x8f\xe5\x90\x8c\xe6\x84\x8f\xe9\x80\x80\xe6\xac\xbe'), (b'WAIT_SELLER_CONFIRM_GOODS', b'\xe4\xb9\xb0\xe5\xae\xb6\xe5\xb7\xb2\xe7\xbb\x8f\xe9\x80\x80\xe8\xb4\xa7'), (b'SELLER_REFUSE_BUYER', b'\xe5\x8d\x96\xe5\xae\xb6\xe6\x8b\x92\xe7\xbb\x9d\xe9\x80\x80\xe6\xac\xbe'), (b'CLOSED', b'\xe9\x80\x80\xe6\xac\xbe\xe5\x85\xb3\xe9\x97\xad'), (b'SUCCESS', b'\xe9\x80\x80\xe6\xac\xbe\xe6\x88\x90\xe5\x8a\x9f')])),
                ('user', models.ForeignKey(related_name='refunds', verbose_name=b'\xe5\xba\x97\xe9\x93\xba', to='users.User', null=True)),
            ],
            options={
                'db_table': 'shop_refunds_refund',
                'verbose_name': '\u9000\u8d27\u6b3e\u5355',
                'verbose_name_plural': '\u9000\u8d27\u6b3e\u5355\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='RefundProduct',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('buyer_nick', models.CharField(db_index=True, max_length=64, verbose_name=b'\xe4\xb9\xb0\xe5\xae\xb6\xe6\x98\xb5\xe7\xa7\xb0', blank=True)),
                ('buyer_mobile', models.CharField(db_index=True, max_length=22, verbose_name=b'\xe6\x89\x8b\xe6\x9c\xba', blank=True)),
                ('buyer_phone', models.CharField(db_index=True, max_length=22, verbose_name=b'\xe5\x9b\xba\xe8\xaf\x9d', blank=True)),
                ('trade_id', models.CharField(default=b'', max_length=64, verbose_name=b'\xe5\x8e\x9f\xe5\x8d\x95ID', db_index=True, blank=True)),
                ('out_sid', models.CharField(db_index=True, max_length=64, verbose_name=b'\xe7\x89\xa9\xe6\xb5\x81\xe5\x8d\x95\xe5\x8f\xb7', blank=True)),
                ('company', models.CharField(db_index=True, max_length=64, verbose_name=b'\xe7\x89\xa9\xe6\xb5\x81\xe5\x90\x8d\xe7\xa7\xb0', blank=True)),
                ('oid', models.CharField(default=b'', max_length=64, verbose_name=b'\xe5\xad\x90\xe8\xae\xa2\xe5\x8d\x95ID', db_index=True, blank=True)),
                ('outer_id', models.CharField(db_index=True, max_length=64, verbose_name=b'\xe5\x95\x86\xe5\x93\x81\xe7\xbc\x96\xe7\xa0\x81', blank=True)),
                ('outer_sku_id', models.CharField(db_index=True, max_length=64, verbose_name=b'\xe8\xa7\x84\xe6\xa0\xbc\xe7\xbc\x96\xe7\xa0\x81', blank=True)),
                ('num', models.IntegerField(default=0, verbose_name=b'\xe6\x95\xb0\xe9\x87\x8f')),
                ('title', models.CharField(max_length=64, verbose_name=b'\xe5\x95\x86\xe5\x93\x81\xe5\x90\x8d\xe7\xa7\xb0', blank=True)),
                ('property', models.CharField(max_length=64, verbose_name=b'\xe8\xa7\x84\xe6\xa0\xbc\xe5\x90\x8d\xe7\xa7\xb0', blank=True)),
                ('can_reuse', models.BooleanField(default=False, verbose_name=b'\xe4\xba\x8c\xe6\xac\xa1\xe9\x94\x80\xe5\x94\xae')),
                ('is_finish', models.BooleanField(default=False, verbose_name=b'\xe5\xa4\x84\xe7\x90\x86\xe5\xae\x8c\xe6\x88\x90')),
                ('reason', models.IntegerField(default=0, verbose_name=b'\xe9\x80\x80\xe8\xb4\xa7\xe5\x8e\x9f\xe5\x9b\xa0', choices=[(0, '\u5176\u4ed6'), (1, '\u9519\u62cd'), (2, '\u7f3a\u8d27'), (3, '\u5f00\u7ebf/\u8131\u8272/\u8131\u6bdb/\u6709\u8272\u5dee/\u6709\u866b\u6d1e'), (4, '\u53d1\u9519\u8d27/\u6f0f\u53d1'), (5, '\u6ca1\u6709\u53d1\u8d27'), (6, '\u672a\u6536\u5230\u8d27'), (7, '\u4e0e\u63cf\u8ff0\u4e0d\u7b26'), (8, '\u9000\u8fd0\u8d39'), (9, '\u53d1\u7968\u95ee\u9898'), (10, '\u4e03\u5929\u65e0\u7406\u7531\u9000\u6362\u8d27')])),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'\xe5\x88\x9b\xe5\xbb\xba\xe6\x97\xb6\xe9\x97\xb4', null=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name=b'\xe4\xbf\xae\xe6\x94\xb9\xe6\x97\xb6\xe9\x97\xb4', null=True)),
                ('memo', models.TextField(max_length=1000, verbose_name=b'\xe5\xa4\x87\xe6\xb3\xa8', blank=True)),
            ],
            options={
                'db_table': 'shop_refunds_product',
                'verbose_name': '\u9000\u8d27\u5546\u54c1',
                'verbose_name_plural': '\u9000\u8d27\u5546\u54c1\u5217\u8868',
            },
        ),
        migrations.AlterUniqueTogether(
            name='refund',
            unique_together=set([('refund_id', 'tid')]),
        ),
    ]
