# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0019_xlmm_carry_total_index'),
    ]

    operations = [
        migrations.AddField(
            model_name='carrytotalrecord',
            name='expect_num',
            field=models.IntegerField(default=0, verbose_name='\u7edf\u8ba1\u671f\u95f4\u9884\u671f\u8ba2\u5355\u6570\u91cf'),
        ),
        migrations.AddField(
            model_name='carrytotalrecord',
            name='expect_total',
            field=models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206\uff0c\u4e0d\u5305\u542bduration_total', verbose_name='\u7edf\u8ba1\u671f\u95f4\u9884\u671f\u6536\u76ca\u603b\u989d'),
        ),
        migrations.AddField(
            model_name='mamacarrytotal',
            name='de_rank_delay',
            field=models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206\uff0c\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0,\u5305\u542bduration_total', verbose_name='\u6d3b\u52a8\u671f\u9884\u671f\u6392\u540d', db_index=True),
        ),
        migrations.AddField(
            model_name='mamacarrytotal',
            name='expect_num',
            field=models.IntegerField(default=0, verbose_name='\u7edf\u8ba1\u671f\u95f4\u9884\u671f\u8ba2\u5355\u6570\u91cf'),
        ),
        migrations.AddField(
            model_name='mamacarrytotal',
            name='expect_total',
            field=models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206\uff0c\u4e0d\u5305\u542bduration_total', verbose_name='\u7edf\u8ba1\u671f\u95f4\u9884\u671f\u6536\u76ca\u603b\u989d'),
        ),
        migrations.AddField(
            model_name='mamacarrytotal',
            name='history_confirm',
            field=models.BooleanField(default=False, help_text='\u5355\u4f4d\u4e3a\u5206', verbose_name='\u5386\u53f2\u6536\u76ca\u786e\u8ba4'),
        ),
        migrations.AddField(
            model_name='mamacarrytotal',
            name='last_renew_type',
            field=models.IntegerField(default=365, db_index=True, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(15, '\u8bd5\u7528'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AddField(
            model_name='mamateamcarrytotal',
            name='de_rank_delay',
            field=models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206\uff0c\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0', verbose_name='\u6d3b\u52a8\u671f\u9884\u671f\u6392\u540d', db_index=True),
        ),
        migrations.AddField(
            model_name='mamateamcarrytotal',
            name='expect_num',
            field=models.IntegerField(default=0, help_text='\u5305\u542b\u4e86duration_num', verbose_name='\u7edf\u8ba1\u671f\u95f4\u9884\u671f\u8ba2\u5355\u6570\u91cf'),
        ),
        migrations.AddField(
            model_name='mamateamcarrytotal',
            name='expect_total',
            field=models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206\uff0c\u5305\u542b\u4e86duration_total', verbose_name='\u7edf\u8ba1\u671f\u95f4\u9884\u671f\u6536\u76ca\u603b\u989d'),
        ),
        migrations.AddField(
            model_name='mamateamcarrytotal',
            name='last_renew_type',
            field=models.IntegerField(default=365, db_index=True, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(15, '\u8bd5\u7528'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AddField(
            model_name='teamcarrytotalrecord',
            name='expect_num',
            field=models.IntegerField(default=0, verbose_name='\u7edf\u8ba1\u671f\u95f4\u9884\u671f\u8ba2\u5355\u6570\u91cf'),
        ),
        migrations.AddField(
            model_name='teamcarrytotalrecord',
            name='expect_total',
            field=models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206', verbose_name='\u7edf\u8ba1\u671f\u95f4\u9884\u671f\u6536\u76ca\u603b\u989d'),
        ),
        migrations.AlterField(
            model_name='agencyorderrebetascheme',
            name='agency_rebetas',
            field=jsonfield.fields.JSONField(default={b'1': 0}, max_length=10240, verbose_name='\u4ee3\u7406\u7b49\u7ea7\u8fd4\u5229\u8bbe\u7f6e', blank=True),
        ),
        migrations.AlterField(
            model_name='agencyorderrebetascheme',
            name='price_active',
            field=models.BooleanField(default=False, verbose_name='\u6839\u636e\u5546\u54c1\u4ef7\u683c\u8fd4\u5229'),
        ),
        migrations.AlterField(
            model_name='agencyorderrebetascheme',
            name='price_rebetas',
            field=jsonfield.fields.JSONField(default={b'1': {b'10': 0}}, max_length=10240, verbose_name='\u5546\u54c1\u4ef7\u683c\u8fd4\u5229\u8bbe\u7f6e', blank=True),
        ),
        migrations.AlterField(
            model_name='carrytotalrecord',
            name='type',
            field=models.IntegerField(default=0, db_index=True, choices=[(0, '\u9ed8\u8ba4'), (1, '\u6d3b\u52a8\u7edf\u8ba1'), (2, '\u6bcf\u5468\u7edf\u8ba1')]),
        ),
        migrations.AlterField(
            model_name='mamacarrytotal',
            name='carry_records',
            field=jsonfield.fields.JSONField(default=b'[]', help_text='\u597d\u50cf\u6ca1\u5565\u7528\u51c6\u5907\u5220\u6389\u4e86', max_length=10240, verbose_name='\u6bcf\u65e5\u6536\u76ca\u5173\u8054', blank=True),
        ),
        migrations.AlterField(
            model_name='xiaolumama',
            name='last_renew_type',
            field=models.IntegerField(default=365, db_index=True, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(15, '\u8bd5\u7528'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
    ]
