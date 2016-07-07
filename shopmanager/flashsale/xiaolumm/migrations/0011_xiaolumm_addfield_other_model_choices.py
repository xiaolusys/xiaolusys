# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0010_add_field_in_xiaolumm'),
    ]

    operations = [
        migrations.AddField(
            model_name='xiaolumama',
            name='is_trial',
            field=models.BooleanField(default=False, verbose_name='\u662f\u5426\u8bd5\u7528'),
        ),
        migrations.AlterField(
            model_name='awardcarry',
            name='status',
            field=models.IntegerField(default=3, verbose_name='\u72b6\u6001', choices=[(1, '\u9884\u8ba1\u6536\u76ca'), (2, '\u786e\u5b9a\u6536\u76ca'), (3, '\u5df2\u53d6\u6d88')]),
        ),
        migrations.AlterField(
            model_name='carryrecord',
            name='status',
            field=models.IntegerField(default=3, verbose_name='\u72b6\u6001', choices=[(1, '\u9884\u8ba1\u6536\u76ca'), (2, '\u786e\u5b9a\u6536\u76ca'), (3, '\u5df2\u53d6\u6d88')]),
        ),
        migrations.AlterField(
            model_name='clickcarry',
            name='status',
            field=models.IntegerField(default=3, verbose_name='\u72b6\u6001', choices=[(1, '\u9884\u8ba1\u6536\u76ca'), (2, '\u786e\u5b9a\u6536\u76ca'), (3, '\u5df2\u53d6\u6d88')]),
        ),
        migrations.AlterField(
            model_name='envelop',
            name='subject',
            field=models.CharField(db_index=True, max_length=8, verbose_name='\u7ea2\u5305\u4e3b\u9898', choices=[(b'cashout', '\u5c0f\u9e7f\u94b1\u5305\u63d0\u73b0'), (b'ordred', '\u8ba2\u5355\u7ea2\u5305'), (b'xlapp', '\u5988\u5988\u94b1\u5305\u63d0\u73b0')]),
        ),
        migrations.AlterField(
            model_name='ordercarry',
            name='status',
            field=models.IntegerField(default=3, verbose_name='\u72b6\u6001', choices=[(0, '\u5f85\u4ed8\u6b3e'), (1, '\u9884\u8ba1\u6536\u76ca'), (2, '\u786e\u5b9a\u6536\u76ca'), (3, '\u4e70\u5bb6\u53d6\u6d88')]),
        ),
        migrations.AlterField(
            model_name='xiaolumama',
            name='agencylevel',
            field=models.IntegerField(default=1, verbose_name='\u4ee3\u7406\u7c7b\u522b', choices=[(1, '\u666e\u901a'), (2, b'VIP1'), (3, 'A\u7c7b'), (12, b'VIP2'), (14, b'VIP4'), (16, b'VIP6'), (18, b'VIP8')]),
        ),
    ]
