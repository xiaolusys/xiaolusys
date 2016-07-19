# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smsmgr', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='smsactivity',
            name='sms_type',
            field=models.CharField(max_length=10, verbose_name='\u7c7b\u578b', choices=[(b'paycall', '\u4ed8\u6b3e\u63d0\u9192'), (b'notify', '\u53d1\u8d27\u901a\u77e5'), (b's_delay', '\u5ef6\u8fdf\u53d1\u8d27\u901a\u77e5'), (b'tocity', '\u540c\u57ce\u63d0\u9192'), (b'sign', '\u7b7e\u6536\u63d0\u9192'), (b'birth', '\u751f\u65e5\u795d\u798f'), (b'activity', '\u6d3b\u52a8\u5ba3\u4f20'), (b'code', '\u9a8c\u8bc1\u7801'), (b'later_send', '\u4e94\u5929\u672a\u53d1\u8d27'), (b'goods_lack', '\u7f3a\u8d27\u901a\u77e5'), (b'lackrefund', '\u7f3a\u8d27\u9000\u6b3e\u901a\u77e5')]),
        ),
        migrations.AlterField(
            model_name='smsrecord',
            name='created',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='\u521b\u5efa\u65f6\u95f4', db_index=True),
        ),
        migrations.AlterField(
            model_name='smsrecord',
            name='mobiles',
            field=models.CharField(default=b'', max_length=64, verbose_name='\u53d1\u9001\u53f7\u7801', db_index=True, blank=True),
        ),
        migrations.AlterField(
            model_name='smsrecord',
            name='status',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u4efb\u52a1\u8fd4\u56de\u7ed3\u679c', choices=[(0, '\u521d\u59cb\u521b\u5efa'), (1, '\u4efb\u52a1\u63d0\u4ea4'), (2, '\u4efb\u52a1\u5b8c\u6210'), (3, '\u4efb\u52a1\u51fa\u9519'), (4, '\u4efb\u52a1\u53d6\u6d88')]),
        ),
        migrations.AlterField(
            model_name='smsrecord',
            name='task_type',
            field=models.CharField(db_index=True, max_length=10, verbose_name='\u7c7b\u578b', choices=[(b'paycall', '\u4ed8\u6b3e\u63d0\u9192'), (b'notify', '\u53d1\u8d27\u901a\u77e5'), (b's_delay', '\u5ef6\u8fdf\u53d1\u8d27\u901a\u77e5'), (b'tocity', '\u540c\u57ce\u63d0\u9192'), (b'sign', '\u7b7e\u6536\u63d0\u9192'), (b'birth', '\u751f\u65e5\u795d\u798f'), (b'activity', '\u6d3b\u52a8\u5ba3\u4f20'), (b'code', '\u9a8c\u8bc1\u7801'), (b'later_send', '\u4e94\u5929\u672a\u53d1\u8d27'), (b'goods_lack', '\u7f3a\u8d27\u901a\u77e5'), (b'lackrefund', '\u7f3a\u8d27\u9000\u6b3e\u901a\u77e5')]),
        ),
    ]
