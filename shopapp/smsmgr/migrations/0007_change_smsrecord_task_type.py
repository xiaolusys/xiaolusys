# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-07 12:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smsmgr', '0006_auto_20161119_1555'),
    ]

    operations = [
        migrations.AlterField(
            model_name='smsactivity',
            name='sms_type',
            field=models.CharField(choices=[('paycall', '\u4ed8\u6b3e\u63d0\u9192'), ('notify', '\u53d1\u8d27\u901a\u77e5'), ('s_delay', '\u5ef6\u8fdf\u53d1\u8d27\u901a\u77e5'), ('code', '\u6ce8\u518c\u9a8c\u8bc1\u7801'), ('reset_code', '\u91cd\u7f6e\u5bc6\u7801\u9a8c\u8bc1\u7801'), ('login_code', '\u767b\u5f55\u9a8c\u8bc1\u7801'), ('cashout_code', '\u63d0\u73b0\u9a8c\u8bc1\u7801'), ('goods_lack', '\u7f3a\u8d27\u9000\u6b3e\u63d0\u9192'), ('appupdate', 'APP\u66f4\u65b0'), ('lackrefund', '\u7f3a\u8d27\u9000\u6b3e\u901a\u77e5'), ('refund_deny', '\u62d2\u7edd\u9000\u6b3e\u7533\u8bf7\u901a\u77e5'), ('refund_approve', '\u540c\u610f\u9000\u6b3e\u8fd4\u6b3e\u901a\u77e5'), ('refund_return', '\u540c\u610f\u9000\u8d27\u7533\u8bf7\u901a\u77e5'), ('refund_ok', '\u9000\u8d27\u9000\u6b3e\u6210\u529f\u63d0\u9192'), ('ordercarry', '\u5988\u5988\u8ba2\u5355\u6536\u76ca\u901a\u77e5'), ('mama_renew', '\u5988\u5988\u7eed\u8d39\u63d0\u9192'), ('sbweixin', '\u63d0\u9192\u5988\u5988\u5173\u6ce8\u5fae\u4fe1'), ('tocity', '\u540c\u57ce\u63d0\u9192')], max_length=16, verbose_name='\u7c7b\u578b'),
        ),
        migrations.AlterField(
            model_name='smsrecord',
            name='task_type',
            field=models.CharField(choices=[('paycall', '\u4ed8\u6b3e\u63d0\u9192'), ('notify', '\u53d1\u8d27\u901a\u77e5'), ('s_delay', '\u5ef6\u8fdf\u53d1\u8d27\u901a\u77e5'), ('code', '\u6ce8\u518c\u9a8c\u8bc1\u7801'), ('reset_code', '\u91cd\u7f6e\u5bc6\u7801\u9a8c\u8bc1\u7801'), ('login_code', '\u767b\u5f55\u9a8c\u8bc1\u7801'), ('cashout_code', '\u63d0\u73b0\u9a8c\u8bc1\u7801'), ('goods_lack', '\u7f3a\u8d27\u9000\u6b3e\u63d0\u9192'), ('appupdate', 'APP\u66f4\u65b0'), ('lackrefund', '\u7f3a\u8d27\u9000\u6b3e\u901a\u77e5'), ('refund_deny', '\u62d2\u7edd\u9000\u6b3e\u7533\u8bf7\u901a\u77e5'), ('refund_approve', '\u540c\u610f\u9000\u6b3e\u8fd4\u6b3e\u901a\u77e5'), ('refund_return', '\u540c\u610f\u9000\u8d27\u7533\u8bf7\u901a\u77e5'), ('refund_ok', '\u9000\u8d27\u9000\u6b3e\u6210\u529f\u63d0\u9192'), ('ordercarry', '\u5988\u5988\u8ba2\u5355\u6536\u76ca\u901a\u77e5'), ('mama_renew', '\u5988\u5988\u7eed\u8d39\u63d0\u9192'), ('sbweixin', '\u63d0\u9192\u5988\u5988\u5173\u6ce8\u5fae\u4fe1'), ('tocity', '\u540c\u57ce\u63d0\u9192')], db_index=True, max_length=16, verbose_name='\u7c7b\u578b'),
        ),
    ]
