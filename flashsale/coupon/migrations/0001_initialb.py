# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import flashsale.coupon.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CouponTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('title', models.CharField(max_length=64, verbose_name='\u4f18\u60e0\u5238\u6807\u9898')),
                ('description', models.CharField(max_length=128, verbose_name='\u4f7f\u7528\u8bf4\u660e')),
                ('value', models.FloatField(default=1.0, verbose_name='\u4f18\u60e0\u5238\u4ef7\u503c')),
                ('is_random_val', models.BooleanField(default=False, db_index=True, verbose_name='\u91d1\u989d\u968f\u673a')),
                ('prepare_release_num', models.IntegerField(default=0, verbose_name='\u8ba1\u5212\u53d1\u653e\u6570\u91cf')),
                ('is_flextime', models.BooleanField(default=False, db_index=True, verbose_name='\u5f39\u6027\u6709\u6548\u65f6\u95f4')),
                ('release_start_time', models.DateTimeField(null=True, verbose_name='\u5f00\u59cb\u53d1\u653e\u7684\u65f6\u95f4', blank=True)),
                ('release_end_time', models.DateTimeField(null=True, verbose_name='\u7ed3\u675f\u53d1\u653e\u7684\u65f6\u95f4', blank=True)),
                ('use_deadline', models.DateTimeField(null=True, verbose_name='\u622a\u6b62\u4f7f\u7528\u7684\u65f6\u95f4', blank=True)),
                ('has_released_count', models.IntegerField(default=0, verbose_name='\u5df2\u9886\u53d6\u6570\u91cf')),
                ('has_used_count', models.IntegerField(default=0, verbose_name='\u5df2\u4f7f\u7528\u6570\u91cf')),
                ('coupon_type', models.IntegerField(default=1, verbose_name='\u4f18\u60e0\u5238\u7c7b\u578b', choices=[(1, '\u666e\u901a\u7c7b\u578b'), (5, '\u4e0b\u5355\u7ea2\u5305'), (2, '\u8ba2\u5355\u5206\u4eab'), (3, '\u63a8\u8350\u4e13\u4eab'), (4, '\u552e\u540e\u8865\u507f')])),
                ('target_user', models.IntegerField(default=1, verbose_name='\u76ee\u6807\u7528\u6237', choices=[(1, '\u6240\u6709\u7528\u6237'), (2, 'VIP\u7c7b\u4ee3\u7406'), (3, 'A\u7c7b\u4ee3\u7406')])),
                ('scope_type', models.IntegerField(default=1, verbose_name='\u4f7f\u7528\u8303\u56f4', choices=[(1, '\u5168\u573a\u901a\u7528'), (2, '\u7c7b\u76ee\u4e13\u7528'), (3, '\u5546\u54c1\u4e13\u7528')])),
                ('status', models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(0, '\u672a\u53d1\u653e'), (1, '\u53d1\u653e\u4e2d'), (2, '\u5df2\u7ed3\u675f'), (3, '\u5df2\u53d6\u6d88')])),
                ('extras', jsonfield.fields.JSONField(default=flashsale.coupon.models.default_template_extras, max_length=512, null=True, verbose_name='\u9644\u52a0\u4fe1\u606f', blank=True)),
            ],
            options={
                'db_table': 'flashsale_coupon_template',
                'verbose_name': '\u7279\u5356/\u4f18\u60e0\u5238/\u6a21\u677f',
                'verbose_name_plural': '\u7279\u5356/\u4f18\u60e0\u5238/\u6a21\u677f\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='OrderShareCoupon',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('template_id', models.IntegerField(verbose_name='\u6a21\u677fID', db_index=True)),
                ('share_customer', models.IntegerField(verbose_name='\u5206\u4eab\u7528\u6237', db_index=True)),
                ('uniq_id', models.CharField(unique=True, max_length=32, verbose_name='\u552f\u4e00ID')),
                ('release_count', models.IntegerField(default=0, verbose_name='\u9886\u53d6\u6b21\u6570')),
                ('has_used_count', models.IntegerField(default=0, verbose_name='\u4f7f\u7528\u6b21\u6570')),
                ('limit_share_count', models.IntegerField(default=0, verbose_name='\u6700\u5927\u9886\u53d6\u6b21\u6570')),
                ('platform_info', jsonfield.fields.JSONField(default=b'{}', max_length=128, verbose_name='\u5206\u4eab\u5230\u5e73\u53f0\u8bb0\u5f55', blank=True)),
                ('share_start_time', models.DateTimeField(verbose_name='\u5206\u4eab\u5f00\u59cb\u65f6\u95f4', blank=True)),
                ('share_end_time', models.DateTimeField(db_index=True, verbose_name='\u5206\u4eab\u622a\u6b62\u65f6\u95f4', blank=True)),
                ('status', models.IntegerField(default=0, db_index=True, verbose_name='\u72b6\u6001', choices=[(0, '\u53d1\u653e\u4e2d'), (1, '\u5df2\u7ed3\u675f')])),
                ('extras', jsonfield.fields.JSONField(default=flashsale.coupon.models.default_share_extras, max_length=1024, null=True, verbose_name='\u9644\u52a0\u4fe1\u606f', blank=True)),
            ],
            options={
                'db_table': 'flashsale_coupon_share_batch',
                'verbose_name': '\u7279\u5356/\u4f18\u60e0\u5238/\u8ba2\u5355\u5206\u4eab\u8868',
                'verbose_name_plural': '\u7279\u5356/\u4f18\u60e0\u5238/\u8ba2\u5355\u5206\u4eab\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='TmpShareCoupon',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('mobile', models.CharField(max_length=11, verbose_name='\u624b\u673a\u53f7', db_index=True)),
                ('share_coupon_id', models.CharField(max_length=32, verbose_name='\u5206\u4eab\u6279\u6b21id', db_index=True)),
                ('status', models.BooleanField(default=False, db_index=True, verbose_name='\u662f\u5426\u9886\u53d6')),
            ],
            options={
                'db_table': 'flashsale_user_tmp_coupon',
                'verbose_name': '\u7279\u5356/\u4f18\u60e0\u5238/\u7528\u6237\u4e34\u65f6\u4f18\u60e0\u5238\u8868',
                'verbose_name_plural': '\u7279\u5356/\u4f18\u60e0\u5238/\u7528\u6237\u4e34\u65f6\u4f18\u60e0\u5238\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='UserCoupon',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('template_id', models.IntegerField(verbose_name='\u4f18\u60e0\u5238id', db_index=True)),
                ('title', models.CharField(max_length=64, verbose_name='\u4f18\u60e0\u5238\u6807\u9898')),
                ('coupon_type', models.IntegerField(default=1, verbose_name='\u4f18\u60e0\u5238\u7c7b\u578b', choices=[(1, '\u666e\u901a\u7c7b\u578b'), (5, '\u4e0b\u5355\u7ea2\u5305'), (2, '\u8ba2\u5355\u5206\u4eab'), (3, '\u63a8\u8350\u4e13\u4eab'), (4, '\u552e\u540e\u8865\u507f')])),
                ('customer_id', models.IntegerField(verbose_name='\u987e\u5ba2ID', db_index=True)),
                ('share_user_id', models.IntegerField(verbose_name='\u5206\u4eab\u7528\u6237ID', db_index=True)),
                ('order_coupon_id', models.IntegerField(verbose_name='\u8ba2\u5355\u4f18\u60e0\u5238\u5206\u4eabID', db_index=True)),
                ('coupon_no', models.CharField(default=flashsale.coupon.models.default_coupon_no, unique=True, max_length=32, verbose_name='\u4f18\u60e0\u5238\u53f7\u7801')),
                ('value', models.FloatField(verbose_name='\u4f18\u60e0\u5238\u4ef7\u503c')),
                ('trade_tid', models.CharField(db_index=True, max_length=32, verbose_name='\u7ed1\u5b9a\u4ea4\u6613tid', blank=True)),
                ('finished_time', models.DateTimeField(db_index=True, null=True, verbose_name='\u4f7f\u7528\u65f6\u95f4', blank=True)),
                ('start_use_time', models.DateTimeField(verbose_name='\u5f00\u59cb\u65f6\u95f4', db_index=True)),
                ('expires_time', models.DateTimeField(verbose_name='\u8fc7\u671f\u65f6\u95f4', db_index=True)),
                ('ufrom', models.CharField(blank=True, max_length=8, verbose_name='\u9886\u53d6\u5e73\u53f0', db_index=True, choices=[('wx', '\u5fae\u4fe1\u597d\u53cb'), ('pyq', '\u670b\u53cb\u5708'), ('qq', 'QQ\u597d\u53cb'), ('qq_spa', 'QQ\u7a7a\u95f4'), ('sina', '\u65b0\u6d6a\u5fae\u535a'), ('wap', 'wap')])),
                ('uniq_id', models.CharField(unique=True, max_length=32, verbose_name='\u4f18\u60e0\u5238\u552f\u4e00\u6807\u8bc6')),
                ('status', models.IntegerField(default=0, verbose_name='\u4f7f\u7528\u72b6\u6001', choices=[(0, '\u672a\u4f7f\u7528'), (1, '\u5df2\u4f7f\u7528'), (2, '\u51bb\u7ed3\u4e2d'), (3, '\u5df2\u7ecf\u8fc7\u671f')])),
                ('extras', jsonfield.fields.JSONField(default=flashsale.coupon.models.default_coupon_extras, max_length=1024, null=True, verbose_name='\u9644\u52a0\u4fe1\u606f', blank=True)),
            ],
            options={
                'db_table': 'flashsale_user_coupon',
                'verbose_name': '\u7279\u5356/\u4f18\u60e0\u5238/\u7528\u6237\u4f18\u60e0\u5238\u8868',
                'verbose_name_plural': '\u7279\u5356/\u4f18\u60e0\u5238/\u7528\u6237\u4f18\u60e0\u5238\u5217\u8868',
            },
        ),
    ]
