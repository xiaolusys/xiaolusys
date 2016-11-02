# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('num_iid', models.BigIntegerField(verbose_name='\u5546\u54c1ID', db_index=True)),
                ('tid', models.BigIntegerField(verbose_name='\u4ea4\u6613ID', db_index=True)),
                ('oid', models.BigIntegerField(verbose_name='\u8ba2\u5355ID', db_index=True)),
                ('item_title', models.CharField(max_length=148, verbose_name='\u5546\u54c1\u6807\u9898', blank=True)),
                ('item_pic_url', models.URLField(verbose_name='\u5546\u54c1\u56fe\u7247', blank=True)),
                ('detail_url', models.URLField(verbose_name='\u8be6\u60c5\u94fe\u63a5', blank=True)),
                ('item_price', models.DecimalField(null=True, verbose_name='\u5546\u54c1\u4ef7\u683c', max_digits=10, decimal_places=2)),
                ('valid_score', models.BooleanField(default=True, verbose_name='\u662f\u5426\u8bb0\u5206')),
                ('role', models.CharField(max_length=8, verbose_name='\u89d2\u8272', choices=[(b'seller', '\u5356\u5bb6'), (b'buyer', '\u4e70\u5bb6')])),
                ('result', models.CharField(blank=True, max_length=8, verbose_name='\u8bc4\u4ef7\u7ed3\u679c', choices=[(b'good', '\u597d\u8bc4'), (b'neutral', '\u4e2d\u8bc4'), (b'bad', '\u5dee\u8bc4')])),
                ('nick', models.CharField(max_length=32, verbose_name='\u8bc4\u4ef7\u8005', blank=True)),
                ('rated_nick', models.CharField(max_length=32, verbose_name='\u88ab\u8bc4\u4ef7\u8005', blank=True)),
                ('content', models.CharField(max_length=1500, verbose_name='\u8bc4\u4ef7\u5185\u5bb9', blank=True)),
                ('reply', models.CharField(max_length=1500, verbose_name='\u8bc4\u4ef7\u89e3\u91ca', blank=True)),
                ('is_reply', models.BooleanField(default=False, verbose_name='\u5df2\u89e3\u91ca')),
                ('ignored', models.BooleanField(default=False, verbose_name='\u5df2\u5ffd\u7565')),
                ('replay_at', models.DateTimeField(db_index=True, null=True, verbose_name='\u89e3\u91ca\u65e5\u671f', blank=True)),
                ('created', models.DateTimeField(null=True, verbose_name='\u521b\u5efa\u65e5\u671f', blank=True)),
                ('replayer', models.ForeignKey(default=None, verbose_name='\u8bc4\u4ef7\u4eba', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'db_table': 'shop_comments_comment',
                'verbose_name': '\u4ea4\u6613\u8bc4\u8bba',
                'verbose_name_plural': '\u4ea4\u6613\u8bc4\u8bba\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='CommentGrade',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('num_iid', models.BigIntegerField(verbose_name='\u5546\u54c1ID')),
                ('tid', models.BigIntegerField(verbose_name='\u4ea4\u6613ID', db_index=True)),
                ('oid', models.BigIntegerField(verbose_name='\u8ba2\u5355ID')),
                ('reply', models.TextField(max_length=1500, verbose_name='\u8bc4\u4ef7\u89e3\u91ca', blank=True)),
                ('created', models.DateTimeField(auto_now=True, verbose_name='\u521b\u5efa\u65e5\u671f', null=True)),
                ('replay_at', models.DateTimeField(db_index=True, null=True, verbose_name='\u89e3\u91ca\u65e5\u671f', blank=True)),
                ('grade', models.IntegerField(default=0, verbose_name='\u8bc4\u4ef7\u6253\u5206', choices=[(1, '\u4f18\u79c0'), (2, '\u5408\u683c'), (0, '\u4e0d\u5408\u683c')])),
                ('grader', models.ForeignKey(related_name='grade_maker', default=None, verbose_name='\u6253\u5206\u4eba', to=settings.AUTH_USER_MODEL, null=True)),
                ('replayer', models.ForeignKey(related_name='grade_replyers', default=None, verbose_name='\u8bc4\u4ef7\u4eba', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'db_table': 'shop_comments_grade',
                'verbose_name': '\u8bc4\u8bba\u6253\u5206',
                'verbose_name_plural': '\u8bc4\u8bba\u6253\u5206\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='CommentItem',
            fields=[
                ('num_iid', models.BigIntegerField(serialize=False, verbose_name='\u5546\u54c1ID', primary_key=True)),
                ('title', models.CharField(max_length=64, verbose_name='\u6807\u9898', blank=True)),
                ('pic_url', models.URLField(verbose_name='\u5546\u54c1\u56fe\u7247', blank=True)),
                ('detail_url', models.URLField(verbose_name='\u8be6\u60c5\u94fe\u63a5', blank=True)),
                ('updated', models.DateTimeField(null=True, verbose_name='\u66f4\u65b0\u65e5\u671f', blank=True)),
                ('is_active', models.BooleanField(default=True, verbose_name='\u6709\u6548')),
            ],
            options={
                'db_table': 'shop_comments_commentitem',
                'verbose_name': '\u8bc4\u4ef7\u5546\u54c1',
                'verbose_name_plural': '\u8bc4\u4ef7\u5546\u54c1\u5217\u8868',
            },
        ),
        migrations.AlterUniqueTogether(
            name='commentgrade',
            unique_together=set([('num_iid', 'tid', 'oid')]),
        ),
        migrations.AlterUniqueTogether(
            name='comment',
            unique_together=set([('num_iid', 'tid', 'oid', 'role')]),
        ),
    ]
