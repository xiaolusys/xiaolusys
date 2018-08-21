# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BranchZone',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(db_index=True, max_length=10, verbose_name=b'\xe7\xbd\x91\xe7\x82\xb9\xe7\xbc\x96\xe5\x8f\xb7', blank=True)),
                ('name', models.CharField(max_length=64, verbose_name=b'\xe7\xbd\x91\xe7\x82\xb9\xe5\x90\x8d\xe7\xa7\xb0', blank=True)),
                ('barcode', models.CharField(max_length=32, verbose_name=b'\xe7\xbd\x91\xe7\x82\xb9\xe6\x9d\xa1\xe7\xa0\x81', blank=True)),
            ],
            options={
                'db_table': 'shop_yunda_branch',
                'verbose_name': '\u97f5\u8fbe\u5206\u62e8\u7f51\u70b9',
                'verbose_name_plural': '\u97f5\u8fbe\u5206\u62e8\u7f51\u70b9',
            },
        ),
        migrations.CreateModel(
            name='ClassifyZone',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('state', models.CharField(db_index=True, max_length=32, verbose_name=b'\xe7\x9c\x81', blank=True)),
                ('city', models.CharField(db_index=True, max_length=32, verbose_name=b'\xe5\xb8\x82', blank=True)),
                ('district', models.CharField(db_index=True, max_length=32, verbose_name=b'\xe5\x8c\xba', blank=True)),
                ('zone', models.CharField(max_length=64, verbose_name=b'\xe9\x9b\x86\xe5\x8c\x85\xe7\xbd\x91\xe7\x82\xb9', blank=True)),
                ('branch', models.ForeignKey(related_name='classify_zones', verbose_name=b'\xe6\x89\x80\xe5\xb1\x9e\xe7\xbd\x91\xe7\x82\xb9', blank=True, to='yunda.BranchZone', null=True)),
            ],
            options={
                'db_table': 'shop_yunda_zone',
                'verbose_name': '\u97f5\u8fbe\u5206\u62e8\u5730\u5740',
                'verbose_name_plural': '\u97f5\u8fbe\u5206\u62e8\u5730\u5740',
            },
        ),
        migrations.CreateModel(
            name='LogisticOrder',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True)),
                ('cus_oid', models.CharField(db_index=True, max_length=64, verbose_name='\u5ba2\u6237\u8ba2\u5355\u7f16\u53f7', blank=True)),
                ('out_sid', models.CharField(unique=True, max_length=64, verbose_name='\u7269\u6d41\u5355\u53f7', blank=True)),
                ('parent_package_id', models.CharField(db_index=True, max_length=64, verbose_name='\u5927\u5305\u7f16\u53f7', blank=True)),
                ('receiver_name', models.CharField(db_index=True, max_length=64, verbose_name='\u6536\u8d27\u4eba\u59d3\u540d', blank=True)),
                ('receiver_state', models.CharField(max_length=16, verbose_name='\u7701', blank=True)),
                ('receiver_city', models.CharField(max_length=16, verbose_name='\u5e02', blank=True)),
                ('receiver_district', models.CharField(max_length=16, verbose_name='\u533a', blank=True)),
                ('receiver_address', models.CharField(max_length=128, verbose_name='\u8be6\u7ec6\u5730\u5740', blank=True)),
                ('receiver_zip', models.CharField(max_length=10, verbose_name='\u90ae\u7f16', blank=True)),
                ('receiver_mobile', models.CharField(db_index=True, max_length=20, verbose_name='\u624b\u673a', blank=True)),
                ('receiver_phone', models.CharField(db_index=True, max_length=20, verbose_name='\u7535\u8bdd', blank=True)),
                ('weight', models.CharField(max_length=10, verbose_name='\u79f0\u91cd(kg)', blank=True)),
                ('upload_weight', models.CharField(max_length=10, verbose_name='\u8ba1\u91cd(kg)', blank=True)),
                ('weighted', models.DateTimeField(default=datetime.datetime.now, verbose_name='\u79f0\u91cd\u65e5\u671f')),
                ('uploaded', models.DateTimeField(null=True, verbose_name='\u4e0a\u4f20\u65e5\u671f', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f')),
                ('valid_code', models.CharField(max_length=4, verbose_name='\u6821\u9a8c\u7801', blank=True)),
                ('dc_code', models.CharField(max_length=8, verbose_name='\u5206\u62e8\u53f7', blank=True)),
                ('is_jzhw', models.BooleanField(default=False, verbose_name='\u6c5f\u6d59\u6caa\u7696')),
                ('is_charged', models.BooleanField(default=False, verbose_name='\u63fd\u4ef6')),
                ('sync_addr', models.BooleanField(default=False, verbose_name='\u5f55\u5355')),
                ('status', models.CharField(default=b'normal', max_length=10, verbose_name='\u72b6\u6001', choices=[(b'normal', '\u6b63\u5e38'), (b'delete', '\u5220\u9664')])),
                ('wave_no', models.CharField(db_index=True, max_length=32, verbose_name='\u6279\u6b21', blank=True)),
            ],
            options={
                'db_table': 'shop_yunda_order',
                'verbose_name': '\u97f5\u8fbe\u8ba2\u5355',
                'verbose_name_plural': '\u97f5\u8fbe\u8ba2\u5355\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='ParentPackageWeight',
            fields=[
                ('parent_package_id', models.CharField(max_length=64, serialize=False, verbose_name='\u5927\u5305\u7f16\u53f7', primary_key=True)),
                ('weight', models.FloatField(default=0.0, verbose_name='\u79f0\u91cd(kg)')),
                ('upload_weight', models.FloatField(default=0.0, verbose_name='\u8ba1\u91cd(kg)')),
                ('weighted', models.DateTimeField(default=datetime.datetime.now, verbose_name='\u79f0\u91cd\u65e5\u671f')),
                ('uploaded', models.DateTimeField(default=datetime.datetime.now, verbose_name='\u4e0a\u4f20\u65e5\u671f')),
                ('destinate', models.CharField(max_length=24, verbose_name='\u96c6\u5305\u5730', blank=True)),
                ('is_jzhw', models.BooleanField(default=False, verbose_name='\u6c5f\u6d59\u6caa\u7696')),
                ('is_charged', models.BooleanField(default=False, verbose_name='\u63fd\u4ef6')),
            ],
            options={
                'db_table': 'shop_yunda_ppw',
                'verbose_name': '\u97f5\u8fbe\u5927\u5305\u91cd\u91cf\u8bb0\u5f55',
                'verbose_name_plural': '\u97f5\u8fbe\u5927\u5305\u91cd\u91cf\u8bb0\u5f55',
            },
        ),
        migrations.CreateModel(
            name='TodayParentPackageWeight',
            fields=[
                ('parent_package_id', models.CharField(max_length=64, serialize=False, verbose_name='\u5927\u5305\u7f16\u53f7', primary_key=True)),
                ('weight', models.FloatField(default=0.0, verbose_name='\u79f0\u91cd(kg)')),
                ('upload_weight', models.FloatField(default=0.0, verbose_name='\u8ba1\u91cd(kg)')),
                ('weighted', models.DateTimeField(default=datetime.datetime.now, verbose_name='\u79f0\u91cd\u65e5\u671f')),
                ('is_jzhw', models.BooleanField(default=False, verbose_name='\u6c5f\u6d59\u6caa\u7696')),
            ],
            options={
                'db_table': 'shop_yunda_tppw',
                'verbose_name': '\u97f5\u8fbe\u5f53\u65e5\u5927\u5305\u91cd\u91cf',
                'verbose_name_plural': '\u97f5\u8fbe\u5f53\u65e5\u5927\u5305\u91cd\u91cf',
            },
        ),
        migrations.CreateModel(
            name='TodaySmallPackageWeight',
            fields=[
                ('package_id', models.CharField(max_length=64, serialize=False, verbose_name='\u8fd0\u5355\u7f16\u53f7', primary_key=True)),
                ('parent_package_id', models.CharField(db_index=True, max_length=64, verbose_name='\u5927\u5305\u7f16\u53f7', blank=True)),
                ('weight', models.FloatField(default=0.0, verbose_name='\u79f0\u91cd(kg)')),
                ('upload_weight', models.FloatField(default=0.0, verbose_name='\u8ba1\u91cd(kg)')),
                ('weighted', models.DateTimeField(default=datetime.datetime.now, verbose_name='\u79f0\u91cd\u65e5\u671f')),
                ('is_jzhw', models.BooleanField(default=False, verbose_name='\u6c5f\u6d59\u6caa\u7696')),
            ],
            options={
                'db_table': 'shop_yunda_tspw',
                'verbose_name': '\u97f5\u8fbe\u5f53\u65e5\u5c0f\u5305\u91cd\u91cf',
                'verbose_name_plural': '\u97f5\u8fbe\u5f53\u65e5\u5c0f\u5305\u91cd\u91cf',
            },
        ),
        migrations.CreateModel(
            name='YundaCustomer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='\u5ba2\u6237\u540d', blank=True)),
                ('code', models.CharField(max_length=16, verbose_name='\u5ba2\u6237\u4ee3\u7801')),
                ('cus_id', models.CharField(max_length=32, verbose_name='\u7f51\u70b9ID', blank=True)),
                ('company_name', models.CharField(max_length=32, verbose_name='\u5ba2\u6237\u516c\u53f8\u540d', blank=True)),
                ('company_trade', models.CharField(max_length=32, verbose_name='\u5ba2\u6237\u7ecf\u8425\u8303\u56f4', blank=True)),
                ('ware_by', models.IntegerField(default=0, verbose_name='\u6240\u5c5e\u4ed3\u5e93')),
                ('qr_id', models.CharField(max_length=32, verbose_name='\u4e8c\u7ef4\u7801\u63a5\u53e3ID', blank=True)),
                ('qr_code', models.CharField(max_length=32, verbose_name='\u4e8c\u7ef4\u7801\u63a5\u53e3\u7801', blank=True)),
                ('lanjian_id', models.CharField(max_length=32, verbose_name='\u63fd\u4ef6ID', blank=True)),
                ('lanjian_code', models.CharField(max_length=32, verbose_name='\u63fd\u4ef6\u7801', blank=True)),
                ('ludan_id', models.CharField(max_length=32, verbose_name='\u5f55\u5355ID', blank=True)),
                ('ludan_code', models.CharField(max_length=32, verbose_name='\u5f55\u5355\u7801', blank=True)),
                ('sn_code', models.CharField(max_length=32, verbose_name='\u8bbe\u5907SN\u7801', blank=True)),
                ('device_code', models.CharField(max_length=32, verbose_name='\u8bbe\u5907\u624b\u673a\u53f7', blank=True)),
                ('contacter', models.CharField(max_length=32, verbose_name='\u8054\u7edc\u4eba', blank=True)),
                ('state', models.CharField(max_length=16, verbose_name='\u7701', blank=True)),
                ('city', models.CharField(max_length=16, verbose_name='\u5e02', blank=True)),
                ('district', models.CharField(max_length=16, verbose_name='\u533a', blank=True)),
                ('address', models.CharField(max_length=128, verbose_name='\u8be6\u7ec6\u5730\u5740', blank=True)),
                ('zip', models.CharField(max_length=10, verbose_name='\u90ae\u7f16', blank=True)),
                ('mobile', models.CharField(db_index=True, max_length=20, verbose_name='\u624b\u673a', blank=True)),
                ('phone', models.CharField(db_index=True, max_length=20, verbose_name='\u7535\u8bdd', blank=True)),
                ('on_qrcode', models.BooleanField(default=False, verbose_name='\u5f00\u542f\u4e8c\u7ef4\u7801')),
                ('on_lanjian', models.BooleanField(default=False, verbose_name='\u5f00\u542f\u63fd\u4ef6')),
                ('on_ludan', models.BooleanField(default=False, verbose_name='\u5f00\u542f\u5f55\u5355')),
                ('on_bpkg', models.BooleanField(default=False, verbose_name='\u5f00\u542f\u96c6\u5305')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f')),
                ('memo', models.CharField(max_length=100, verbose_name='\u5907\u6ce8', blank=True)),
                ('reserveo', models.CharField(max_length=64, verbose_name='\u81ea\u5b9a\u4e491', blank=True)),
                ('reservet', models.CharField(max_length=64, verbose_name='\u81ea\u5b9a\u4e492', blank=True)),
                ('status', models.CharField(default=b'normal', max_length=10, verbose_name='\u72b6\u6001', choices=[(b'normal', '\u6b63\u5e38'), (b'delete', '\u5220\u9664')])),
            ],
            options={
                'db_table': 'shop_yunda_customer',
                'verbose_name': '\u97f5\u8fbe\u5ba2\u6237',
                'verbose_name_plural': '\u97f5\u8fbe\u5ba2\u6237\u5217\u8868',
            },
        ),
        migrations.AlterUniqueTogether(
            name='yundacustomer',
            unique_together=set([('code', 'ware_by')]),
        ),
        migrations.AddField(
            model_name='logisticorder',
            name='yd_customer',
            field=models.ForeignKey(verbose_name='\u6240\u5c5e\u5ba2\u6237', to='yunda.YundaCustomer'),
        ),
    ]
