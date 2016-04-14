# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SMSActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sms_type', models.CharField(max_length=10, verbose_name=b'\xe7\xb1\xbb\xe5\x9e\x8b', choices=[(b'paycall', '\u4ed8\u6b3e\u63d0\u9192'), (b'notify', '\u53d1\u8d27\u901a\u77e5'), (b'tocity', '\u540c\u57ce\u63d0\u9192'), (b'sign', '\u7b7e\u6536\u63d0\u9192'), (b'birth', '\u751f\u65e5\u795d\u798f'), (b'activity', '\u6d3b\u52a8\u5ba3\u4f20'), (b'code', '\u9a8c\u8bc1\u7801'), (b'later_send', '\u4e94\u5929\u672a\u53d1\u8d27'), (b'goods_lack', '\u7f3a\u8d27\u901a\u77e5')])),
                ('text_tmpl', models.CharField(max_length=512, null=True, verbose_name=b'\xe5\x86\x85\xe5\xae\xb9', blank=True)),
                ('status', models.BooleanField(default=True, verbose_name=b'\xe4\xbd\xbf\xe7\x94\xa8')),
            ],
            options={
                'db_table': 'shop_smsmgr_activity',
                'verbose_name': '\u77ed\u4fe1\u6a21\u677f',
                'verbose_name_plural': '\u77ed\u4fe1\u6a21\u677f\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='SMSPlatform',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=16, verbose_name=b'\xe7\xbc\x96\xe7\xa0\x81')),
                ('name', models.CharField(max_length=64, verbose_name=b'\xe6\x9c\x8d\xe5\x8a\xa1\xe5\x95\x86\xe5\x90\x8d\xe7\xa7\xb0')),
                ('user_id', models.CharField(max_length=32, verbose_name=b'\xe4\xbc\x81\xe4\xb8\x9aID')),
                ('account', models.CharField(max_length=64, verbose_name=b'\xe5\xb8\x90\xe5\x8f\xb7')),
                ('password', models.CharField(max_length=64, verbose_name=b'\xe5\xaf\x86\xe7\xa0\x81')),
                ('remainums', models.IntegerField(default=0, verbose_name=b'\xe5\x89\xa9\xe4\xbd\x99\xe6\x9d\xa1\xe6\x95\xb0')),
                ('sendnums', models.IntegerField(default=0, verbose_name=b'\xe5\xb7\xb2\xe5\x8f\x91\xe6\x9d\xa1\xe6\x95\xb0')),
                ('is_default', models.BooleanField(default=False, verbose_name=b'\xe9\xa6\x96\xe9\x80\x89\xe6\x9c\x8d\xe5\x8a\xa1\xe5\x95\x86')),
            ],
            options={
                'db_table': 'shop_smsmgr_smsplatform',
                'verbose_name': '\u77ed\u4fe1\u670d\u52a1\u5546',
                'verbose_name_plural': '\u77ed\u4fe1\u670d\u52a1\u5546\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='SMSRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('task_type', models.CharField(max_length=10, verbose_name=b'\xe7\xb1\xbb\xe5\x9e\x8b', choices=[(b'paycall', '\u4ed8\u6b3e\u63d0\u9192'), (b'notify', '\u53d1\u8d27\u901a\u77e5'), (b'tocity', '\u540c\u57ce\u63d0\u9192'), (b'sign', '\u7b7e\u6536\u63d0\u9192'), (b'birth', '\u751f\u65e5\u795d\u798f'), (b'activity', '\u6d3b\u52a8\u5ba3\u4f20'), (b'code', '\u9a8c\u8bc1\u7801'), (b'later_send', '\u4e94\u5929\u672a\u53d1\u8d27'), (b'goods_lack', '\u7f3a\u8d27\u901a\u77e5')])),
                ('task_id', models.CharField(default=b'', max_length=128, null=True, verbose_name=b'\xe6\x9c\x8d\xe5\x8a\xa1\xe5\x95\x86\xe8\xbf\x94\xe5\x9b\x9e\xe4\xbb\xbb\xe5\x8a\xa1ID', blank=True)),
                ('task_name', models.CharField(default=b'', max_length=256, null=True, verbose_name=b'\xe4\xbb\xbb\xe5\x8a\xa1\xe6\xa0\x87\xe9\xa2\x98', blank=True)),
                ('mobiles', models.TextField(default=b'', null=True, verbose_name=b'\xe5\x8f\x91\xe9\x80\x81\xe5\x8f\xb7\xe7\xa0\x81', blank=True)),
                ('content', models.CharField(default=b'', max_length=1000, null=True, verbose_name=b'\xe5\x8f\x91\xe9\x80\x81\xe5\x86\x85\xe5\xae\xb9', blank=True)),
                ('sendtime', models.DateTimeField(null=True, verbose_name=b'\xe5\xae\x9a\xe6\x97\xb6\xe5\x8f\x91\xe9\x80\x81\xe6\x97\xb6\xe9\x97\xb4', blank=True)),
                ('countnums', models.IntegerField(default=0, verbose_name=b'\xe5\x8f\x91\xe9\x80\x81\xe6\x95\xb0\xe9\x87\x8f')),
                ('mobilenums', models.IntegerField(default=0, verbose_name=b'\xe6\x89\x8b\xe6\x9c\xba\xe6\x95\xb0\xe9\x87\x8f')),
                ('telephnums', models.IntegerField(default=0, verbose_name=b'\xe5\x9b\xba\xe8\xaf\x9d\xe6\x95\xb0\xe9\x87\x8f')),
                ('succnums', models.IntegerField(default=0, verbose_name=b'\xe6\x88\x90\xe5\x8a\x9f\xe6\x95\xb0\xe9\x87\x8f')),
                ('retmsg', models.CharField(max_length=512, null=True, verbose_name=b'\xe4\xbb\xbb\xe5\x8a\xa1\xe8\xbf\x94\xe5\x9b\x9e\xe7\xbb\x93\xe6\x9e\x9c', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'\xe5\x88\x9b\xe5\xbb\xba\xe6\x97\xb6\xe9\x97\xb4', null=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name=b'\xe4\xbf\xae\xe6\x94\xb9\xe6\x97\xb6\xe9\x97\xb4', null=True)),
                ('memo', models.CharField(max_length=512, null=True, verbose_name=b'\xe5\xa4\x87\xe6\xb3\xa8\xe8\xaf\xb4\xe6\x98\x8e', blank=True)),
                ('status', models.IntegerField(default=0, verbose_name=b'\xe4\xbb\xbb\xe5\x8a\xa1\xe8\xbf\x94\xe5\x9b\x9e\xe7\xbb\x93\xe6\x9e\x9c', choices=[(0, b'\xe5\x88\x9d\xe5\xa7\x8b\xe5\x88\x9b\xe5\xbb\xba'), (1, b'\xe4\xbb\xbb\xe5\x8a\xa1\xe6\x8f\x90\xe4\xba\xa4'), (2, b'\xe4\xbb\xbb\xe5\x8a\xa1\xe5\xae\x8c\xe6\x88\x90'), (3, b'\xe4\xbb\xbb\xe5\x8a\xa1\xe5\x87\xba\xe9\x94\x99'), (4, b'\xe4\xbb\xbb\xe5\x8a\xa1\xe5\x8f\x96\xe6\xb6\x88')])),
                ('platform', models.ForeignKey(related_name='sms_records', default=None, verbose_name=b'\xe7\x9f\xad\xe4\xbf\xa1\xe6\x9c\x8d\xe5\x8a\xa1\xe5\x95\x86', to='smsmgr.SMSPlatform', null=True)),
            ],
            options={
                'db_table': 'shop_smsmgr_smsrecord',
                'verbose_name': '\u77ed\u4fe1\u8bb0\u5f55',
                'verbose_name_plural': '\u77ed\u4fe1\u8bb0\u5f55\u5217\u8868',
            },
        ),
    ]
