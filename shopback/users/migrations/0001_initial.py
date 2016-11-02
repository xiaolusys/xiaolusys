# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nick', models.CharField(max_length=32, verbose_name=b'\xe6\x98\xb5\xe7\xa7\xb0')),
                ('sex', models.CharField(max_length=1, verbose_name=b'\xe6\x80\xa7\xe5\x88\xab', blank=True)),
                ('avatar', models.CharField(max_length=32, verbose_name=b'\xe5\xa4\xb4\xe5\x83\x8f', blank=True)),
                ('credit_level', models.IntegerField(default=0, verbose_name=b'\xe4\xbf\xa1\xe7\x94\xa8\xe7\xad\x89\xe7\xba\xa7')),
                ('credit_score', models.IntegerField(default=0, verbose_name=b'\xe4\xbf\xa1\xe7\x94\xa8\xe7\xa7\xaf\xe5\x88\x86')),
                ('credit_total_num', models.IntegerField(default=0, verbose_name=b'\xe6\x80\xbb\xe8\xaf\x84\xe4\xbb\xb7\xe6\x95\xb0')),
                ('credit_good_num', models.IntegerField(default=0, verbose_name=b'\xe5\xa5\xbd\xe8\xaf\x84\xe6\x95\xb0')),
                ('name', models.CharField(db_index=True, max_length=32, verbose_name=b'\xe6\x94\xb6\xe8\xb4\xa7\xe4\xba\xba', blank=True)),
                ('zip', models.CharField(max_length=10, verbose_name=b'\xe9\x82\xae\xe7\xbc\x96', blank=True)),
                ('address', models.CharField(max_length=128, verbose_name=b'\xe5\x9c\xb0\xe5\x9d\x80', blank=True)),
                ('city', models.CharField(max_length=16, verbose_name=b'\xe5\x9f\x8e\xe5\xb8\x82', blank=True)),
                ('state', models.CharField(max_length=16, verbose_name=b'\xe7\x9c\x81', blank=True)),
                ('country', models.CharField(max_length=16, verbose_name=b'\xe5\x9b\xbd\xe5\xae\xb6', blank=True)),
                ('district', models.CharField(max_length=16, verbose_name=b'\xe5\x9c\xb0\xe5\x8c\xba', blank=True)),
                ('phone', models.CharField(max_length=16, null=True, verbose_name=b'\xe7\x94\xb5\xe8\xaf\x9d', blank=True)),
                ('mobile', models.CharField(max_length=12, null=True, verbose_name=b'\xe6\x89\x8b\xe6\x9c\xba', blank=True)),
                ('created', models.DateTimeField(auto_now=True, null=True, verbose_name=b'\xe5\x88\x9b\xe5\xbb\xba\xe6\x97\xa5\xe6\x9c\x9f', db_index=True)),
                ('birthday', models.DateTimeField(db_index=True, null=True, verbose_name=b'\xe7\x94\x9f\xe6\x97\xa5', blank=True)),
                ('last_buy_time', models.DateTimeField(db_index=True, null=True, verbose_name=b'\xe6\x9c\x80\xe5\x90\x8e\xe8\xb4\xad\xe4\xb9\xb0\xe6\x97\xa5\xe6\x9c\x9f', blank=True)),
                ('buy_times', models.IntegerField(default=0, verbose_name=b'\xe8\xb4\xad\xe4\xb9\xb0\xe6\xac\xa1\xe6\x95\xb0')),
                ('avg_payment', models.FloatField(default=0.0, verbose_name=b'\xe5\x9d\x87\xe5\x8d\x95\xe9\x87\x91\xe9\xa2\x9d')),
                ('vip_info', models.CharField(max_length=3, verbose_name=b'VIP\xe7\xad\x89\xe7\xba\xa7', blank=True)),
                ('email', models.CharField(max_length=32, verbose_name=b'\xe9\x82\xae\xe7\xae\xb1', blank=True)),
                ('is_valid', models.BooleanField(default=True, verbose_name='\u6709\u6548')),
            ],
            options={
                'db_table': 'shop_users_customer',
                'verbose_name': '\u4f1a\u5458',
                'verbose_name_plural': '\u4f1a\u5458\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('top_session', models.CharField(max_length=128, verbose_name='SessionID', blank=True)),
                ('top_appkey', models.CharField(max_length=32, verbose_name='AppKey', blank=True)),
                ('top_parameters', models.TextField(max_length=2000, verbose_name='\u8bbf\u95ee\u53c2\u6570', blank=True)),
                ('visitor_id', models.CharField(db_index=True, max_length=64, verbose_name='\u5e97\u94faID', blank=True)),
                ('uid', models.CharField(max_length=64, verbose_name='\u7528\u6237ID', blank=True)),
                ('nick', models.CharField(max_length=64, verbose_name='\u5e97\u94fa\u540d', blank=True)),
                ('user_code', models.CharField(max_length=16, verbose_name='\u5185\u90e8\u7f16\u7801', blank=True)),
                ('sex', models.CharField(max_length=1, blank=True)),
                ('contacter', models.CharField(max_length=32, verbose_name='\u8054\u7edc\u4eba', blank=True)),
                ('phone', models.CharField(max_length=20, verbose_name='\u7535\u8bdd', blank=True)),
                ('mobile', models.CharField(max_length=20, verbose_name='\u624b\u673a', blank=True)),
                ('area_code', models.CharField(max_length=10, verbose_name='\u533a\u53f7', blank=True)),
                ('buyer_credit', models.CharField(max_length=80, verbose_name='\u4e70\u5bb6\u4fe1\u7528', blank=True)),
                ('seller_credit', models.CharField(max_length=80, verbose_name='\u5356\u5bb6\u4fe1\u7528', blank=True)),
                ('has_fenxiao', models.BooleanField(default=False, verbose_name='\u7ba1\u7406\u5206\u9500')),
                ('location', models.CharField(max_length=256, verbose_name='\u5e97\u94fa\u5730\u5740', blank=True)),
                ('created', models.CharField(max_length=19, blank=True)),
                ('birthday', models.CharField(max_length=19, blank=True)),
                ('type', models.CharField(blank=True, max_length=8, verbose_name='\u5e97\u94fa\u7c7b\u578b', choices=[(b'B', '\u6dd8\u5b9d\u5546\u57ce'), (b'C', '\u6dd8\u5b9dC\u5e97'), (b'JD', '\u4eac\u4e1c'), (b'SALE', '\u5c0f\u9e7f\u7279\u5356'), (b'YHD', '\u4e00\u53f7\u5e97'), (b'DD', '\u5f53\u5f53'), (b'SN', '\u82cf\u5b81'), (b'WX', '\u5fae\u4fe1\u5c0f\u5e97'), (b'AMZ', '\u4e9a\u9a6c\u900a'), (b'OTHER', '\u5176\u5b83')])),
                ('item_img_num', models.IntegerField(default=0, verbose_name='\u5546\u54c1\u56fe\u7247\u6570\u91cf')),
                ('item_img_size', models.IntegerField(default=0, verbose_name='\u5546\u54c1\u56fe\u7247\u5c3a\u5bf8')),
                ('prop_img_num', models.IntegerField(default=0, verbose_name='\u53ef\u4e0a\u4f20\u5c5e\u6027\u56fe\u7247\u6570\u91cf')),
                ('prop_img_size', models.IntegerField(default=0, verbose_name='\u53ef\u4e0a\u4f20\u5c5e\u6027\u56fe\u7247\u5c3a\u5bf8')),
                ('auto_repost', models.CharField(max_length=16, verbose_name='\u662f\u5426\u53d7\u9650', blank=True)),
                ('alipay_bind', models.CharField(max_length=10, verbose_name='\u652f\u4ed8\u5b9d\u7ed1\u5b9a', blank=True)),
                ('alipay_no', models.CharField(max_length=20, verbose_name='\u652f\u4ed8\u5b9d\u5e10\u53f7', blank=True)),
                ('sync_stock', models.BooleanField(default=True, verbose_name='\u540c\u6b65\u5e93\u5b58')),
                ('percentage', models.IntegerField(default=0, verbose_name='\u5e93\u5b58\u540c\u6b65\u6bd4\u4f8b')),
                ('is_primary', models.BooleanField(default=False, verbose_name='\u4e3b\u5e97\u94fa')),
                ('created_at', models.DateTimeField(auto_now=True, verbose_name='\u521b\u5efa\u65e5\u671f', null=True)),
                ('status', models.CharField(default=b'normal', max_length=12, verbose_name='\u72b6\u6001', choices=[(b'normal', '\u6b63\u5e38'), (b'inactive', '\u672a\u6fc0\u6d3b'), (b'delete', '\u5220\u9664'), (b'freeze', '\u51bb\u7ed3'), (b'supervise', '\u76d1\u7ba1')])),
                ('user', models.ForeignKey(verbose_name='\u5173\u8054\u7528\u6237', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'db_table': 'shop_users_user',
                'verbose_name': '\u5e97\u94fa',
                'verbose_name_plural': '\u5e97\u94fa\u5217\u8868',
                'permissions': [('can_download_orderinfo', '\u4e0b\u8f7d\u5f85\u53d1\u8d27\u8ba2\u5355'), ('can_download_iteminfo', '\u4e0b\u8f7d\u7ebf\u4e0a\u5546\u54c1\u4fe1\u606f'), ('can_manage_itemlist', '\u7ba1\u7406\u5546\u54c1\u4e0a\u67b6\u65f6\u95f4'), ('can_recover_instock', '\u7ebf\u4e0a\u5e93\u5b58\u8986\u76d6\u7cfb\u7edf\u5e93\u5b58'), ('can_async_threemtrade', '\u5f02\u6b65\u4e0b\u8f7d\u8fd1\u4e09\u6708\u8ba2\u5355')],
            },
        ),
        migrations.AlterUniqueTogether(
            name='customer',
            unique_together=set([('nick', 'mobile', 'phone')]),
        ),
    ]
