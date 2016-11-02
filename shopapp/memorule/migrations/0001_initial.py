# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ComposeItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('outer_id', models.CharField(db_index=True, max_length=64, verbose_name='\u7ec4\u5408\u5546\u54c1\u5916\u90e8\u7f16\u7801', blank=True)),
                ('outer_sku_id', models.CharField(db_index=True, max_length=64, verbose_name='\u7ec4\u5408\u5546\u54c1\u89c4\u683c\u7f16\u7801', blank=True)),
                ('num', models.IntegerField(default=1, verbose_name='\u5546\u54c1\u6570\u91cf')),
                ('extra_info', models.TextField(verbose_name='\u4fe1\u606f', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified', models.DateTimeField(auto_now=True, null=True)),
            ],
            options={
                'db_table': 'shop_memorule_composeitem',
                'verbose_name': '\u62c6\u5206\u89c4\u5219\u5546\u54c1',
                'verbose_name_plural': '\u62c6\u5206\u89c4\u5219\u5546\u54c1\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='ComposeRule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('outer_id', models.CharField(db_index=True, max_length=64, verbose_name='\u5546\u54c1\u5916\u90e8\u7f16\u7801', blank=True)),
                ('outer_sku_id', models.CharField(db_index=True, max_length=64, verbose_name='\u5546\u54c1\u89c4\u683c\u7f16\u7801', blank=True)),
                ('seller_id', models.IntegerField(default=0, verbose_name='\u5356\u5bb6ID')),
                ('payment', models.IntegerField(default=0, null=True, verbose_name='\u91d1\u989d')),
                ('type', models.CharField(max_length=10, verbose_name='\u89c4\u5219\u7c7b\u578b', choices=[(b'payment', b'\xe6\xbb\xa1\xe5\xb0\xb1\xe9\x80\x81'), (b'product', b'\xe7\xbb\x84\xe5\x90\x88\xe6\x8b\x86\xe5\x88\x86'), (b'gifts', b'\xe4\xb9\xb0\xe5\xb0\xb1\xe9\x80\x81')])),
                ('gif_count', models.IntegerField(default=0, verbose_name='\u5269\u4f59\u540d\u989d')),
                ('scb_count', models.IntegerField(default=0, verbose_name='\u5df2\u9001\u540d\u989d')),
                ('extra_info', models.TextField(verbose_name='\u4fe1\u606f', blank=True)),
                ('start_time', models.DateTimeField(null=True, verbose_name='\u5f00\u59cb\u65f6\u95f4', blank=True)),
                ('end_time', models.DateTimeField(null=True, verbose_name='\u7ed3\u675f\u65f6\u95f4', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65f6\u95f4', null=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65f6\u95f4', null=True)),
                ('status', models.BooleanField(default=False, verbose_name='\u751f\u6548')),
            ],
            options={
                'db_table': 'shop_memorule_composerule',
                'verbose_name': '\u5339\u914d\u89c4\u5219',
                'verbose_name_plural': '\u62c6\u5206\u89c4\u5219\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='InterceptTrade',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('buyer_nick', models.CharField(db_index=True, max_length=64, verbose_name='\u4e70\u5bb6\u6635\u79f0', blank=True)),
                ('buyer_mobile', models.CharField(db_index=True, max_length=24, verbose_name='\u624b\u673a', blank=True)),
                ('serial_no', models.CharField(db_index=True, max_length=64, verbose_name='\u5916\u90e8\u5355\u53f7', blank=True)),
                ('trade_id', models.BigIntegerField(null=True, verbose_name='\u7cfb\u7edf\u8ba2\u5355ID', blank=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65f6\u95f4', null=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', null=True)),
                ('status', models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(0, '\u672a\u62e6\u622a'), (1, '\u5df2\u62e6\u622a')])),
            ],
            options={
                'db_table': 'shop_intercept_trade',
                'verbose_name': '\u62e6\u622a\u8ba2\u5355',
                'verbose_name_plural': '\u62e6\u622a\u8ba2\u5355\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='ProductRuleField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('outer_id', models.CharField(max_length=64, db_index=True)),
                ('custom_alias', models.CharField(max_length=256, blank=True)),
                ('custom_default', models.TextField(max_length=256, blank=True)),
            ],
            options={
                'db_table': 'shop_memorule_productrulefield',
                'verbose_name': '\u5f85\u5ba1\u6838\u89c4\u5219',
            },
        ),
        migrations.CreateModel(
            name='RuleFieldType',
            fields=[
                ('field_name', models.CharField(max_length=64, serialize=False, primary_key=True)),
                ('field_type', models.CharField(max_length=10, choices=[(b'single', b'\xe5\x8d\x95\xe9\x80\x89'), (b'check', b'\xe5\xa4\x8d\xe9\x80\x89'), (b'text', b'\xe6\x96\x87\xe6\x9c\xac')])),
                ('alias', models.CharField(max_length=64)),
                ('default_value', models.TextField(max_length=256, blank=True)),
            ],
            options={
                'db_table': 'shop_memorule_rulefieldtype',
            },
        ),
        migrations.CreateModel(
            name='RuleMemo',
            fields=[
                ('tid', models.BigIntegerField(serialize=False, primary_key=True)),
                ('is_used', models.BooleanField(default=False)),
                ('rule_memo', models.TextField(max_length=1000, blank=True)),
                ('seller_flag', models.IntegerField(null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified', models.DateTimeField(auto_now=True, null=True)),
            ],
            options={
                'db_table': 'shop_memorule_rulememo',
            },
        ),
        migrations.CreateModel(
            name='TradeRule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('formula', models.CharField(max_length=64, blank=True)),
                ('memo', models.CharField(max_length=64, blank=True)),
                ('formula_desc', models.TextField(max_length=256, blank=True)),
                ('scope', models.CharField(max_length=10, choices=[(b'trade', b'\xe4\xba\xa4\xe6\x98\x93\xe5\x9f\x9f'), (b'product', b'\xe5\x95\x86\xe5\x93\x81\xe5\x9f\x9f')])),
                ('status', models.CharField(max_length=2, choices=[(b'US', b'\xe4\xbd\xbf\xe7\x94\xa8'), (b'SX', b'\xe5\xa4\xb1\xe6\x95\x88')])),
                ('items', models.ManyToManyField(related_name='rules', db_table=b'shop_memorule_itemrulemap', to='items.Item')),
            ],
            options={
                'db_table': 'shop_memorule_traderule',
            },
        ),
        migrations.AddField(
            model_name='productrulefield',
            name='field',
            field=models.ForeignKey(to='memorule.RuleFieldType'),
        ),
        migrations.AlterUniqueTogether(
            name='composerule',
            unique_together=set([('outer_id', 'outer_sku_id', 'type')]),
        ),
        migrations.AddField(
            model_name='composeitem',
            name='compose_rule',
            field=models.ForeignKey(related_name='compose_items', verbose_name='\u5546\u54c1\u89c4\u5219', to='memorule.ComposeRule'),
        ),
    ]
