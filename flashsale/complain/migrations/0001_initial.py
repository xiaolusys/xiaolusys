# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Complain',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('com_type', models.IntegerField(default=3, verbose_name='\u7c7b\u578b', choices=[(0, '\u8d2d\u7269\u95ee\u9898'), (1, '\u8ba2\u5355\u76f8\u5173'), (4, '\u552e\u540e\u95ee\u9898'), (2, '\u610f\u89c1/\u5efa\u8bae'), (3, '\u5176\u4ed6')])),
                ('insider_phone', models.CharField(db_index=True, max_length=32, verbose_name='\u6295\u8bc9\u4ebaID', blank=True)),
                ('com_title', models.CharField(default='\u95ee\u9898\u53cd\u9988', max_length=64, verbose_name='\u6807\u9898', db_index=True, blank=True)),
                ('com_content', models.TextField(max_length=1024, verbose_name='\u5185\u5bb9', blank=True)),
                ('contact_way', models.CharField(max_length=128, verbose_name='\u8054\u7cfb\u65b9\u5f0f', blank=True)),
                ('created_time', models.DateField(auto_now_add=True, verbose_name='\u6295\u8bc9\u65f6\u95f4', null=True)),
                ('status', models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(0, '\u672a\u5904\u7406'), (1, '\u5df2\u5904\u7406'), (2, '\u5df2\u4f5c\u5e9f'), (3, '\u5df2\u5220\u9664')])),
                ('custom_serviced', models.CharField(max_length=32, verbose_name='\u5ba2\u670d\u53f7', blank=True)),
                ('reply', models.CharField(max_length=1024, verbose_name='\u56de\u590d', blank=True)),
                ('reply_time', models.DateTimeField(null=True, verbose_name='\u56de\u590d\u65f6\u95f4', blank=True)),
            ],
            options={
                'ordering': ('created_time', 'insider_phone'),
                'db_table': 'complain',
                'verbose_name': '\u95ee\u9898\u53cd\u9988',
                'verbose_name_plural': '\u6295\u8bc9\u5efa\u8bae\u8868',
            },
        ),
    ]
