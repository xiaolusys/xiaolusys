# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('choice_title', models.CharField(max_length=200, verbose_name='\u9009\u9879\u7f16\u53f7')),
                ('choice_text', models.CharField(max_length=200, verbose_name='\u9009\u9879\u63cf\u8ff0')),
                ('choice_score', models.IntegerField(default=0, verbose_name='\u5206\u503c')),
            ],
            options={
                'db_table': 'flashsale_mmexam_choice',
                'verbose_name': '\u4ee3\u7406\u8003\u8bd5\u9009\u9879',
                'verbose_name_plural': '\u4ee3\u7406\u8003\u8bd5\u9009\u9879\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('question', models.CharField(max_length=200, verbose_name='\u95ee\u9898')),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='\u51fa\u5377\u65e5\u671f', null=True)),
                ('real_answer', models.CharField(max_length=200, verbose_name='\u6b63\u786e\u9009\u9879(\u8bf7\u6309\u7167\u987a\u5e8f\u8f93\u5165)')),
                ('single_many', models.IntegerField(verbose_name='\u5355\u9009/\u591a\u9009', choices=[(1, '\u5355\u9009'), (2, '\u591a\u9009')])),
            ],
            options={
                'db_table': 'flashsale_mmexam_question',
                'verbose_name': '\u4ee3\u7406\u8003\u8bd5\u9898\u76ee',
                'verbose_name_plural': '\u4ee3\u7406\u8003\u8bd5\u9898\u76ee\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('daili_user', models.CharField(unique=True, max_length=32, verbose_name='\u4ee3\u7406unionid')),
                ('exam_date', models.DateTimeField(auto_now_add=True, verbose_name='\u7b54\u9898\u65e5\u671f', null=True)),
                ('exam_state', models.IntegerField(default=0, verbose_name='\u662f\u5426\u901a\u8fc7', choices=[(0, '\u672a\u901a\u8fc7'), (1, '\u5df2\u901a\u8fc7')])),
            ],
            options={
                'db_table': 'flashsale_mmexam_result',
                'verbose_name': '\u4ee3\u7406\u8003\u8bd5\u7ed3\u679c',
                'verbose_name_plural': '\u4ee3\u7406\u8003\u8bd5\u7ed3\u679c\u5217\u8868',
            },
        ),
        migrations.AddField(
            model_name='choice',
            name='question',
            field=models.ForeignKey(to='mmexam.Question'),
        ),
    ]
