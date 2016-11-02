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
            name='ExamEssayQuestionPaper',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('paper_id', models.CharField(max_length=100, null=True, db_index=True)),
                ('problem_id', models.IntegerField(verbose_name='\u9898\u7801', db_index=True)),
                ('exam_answer', models.CharField(max_length=6000, verbose_name='\u9009\u9879', blank=True)),
                ('exam_selected', models.CharField(max_length=6000, verbose_name='\u7b54\u9898\u4eba\u9009\u9879', blank=True)),
                ('exam_problem_score', models.IntegerField(null=True, verbose_name='\u9898\u76ee\u5206\u6570', db_index=True)),
            ],
            options={
                'db_table': 'shop_examination_paper_essay_question',
                'verbose_name': '\u8003\u8bd5wenda\u5377\u4fe1\u606f',
                'verbose_name_plural': '\u8003\u8bd5wenda\u5377\u4fe1\u606f\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='ExamProblemSelect',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('exam_problem', models.CharField(max_length=1500, verbose_name='\u9898\u76ee', blank=True)),
                ('exam_answer', models.CharField(max_length=4, verbose_name='\u6b63\u786e\u9009\u9879', blank=True)),
                ('option_a', models.CharField(max_length=200, verbose_name='\u9009\u9879A', blank=True)),
                ('option_b', models.CharField(max_length=200, verbose_name='\u9009\u9879B', blank=True)),
                ('option_c', models.CharField(max_length=200, verbose_name='\u9009\u9879C', blank=True)),
                ('option_d', models.CharField(max_length=200, verbose_name='\u9009\u9879D', blank=True)),
                ('exam_problem_score', models.IntegerField(null=True, verbose_name='\u9898\u76ee\u5206\u6570', db_index=True)),
                ('exam_problem_created', models.DateTimeField(null=True, verbose_name='\u521b\u5efa\u65e5\u671f', blank=True)),
            ],
            options={
                'db_table': 'shop_examination_problem_select',
                'verbose_name': '\u8003\u8bd5\u9898\u5e93',
                'verbose_name_plural': '\u8003\u8bd5\u9898\u5e93\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='ExamSelectProblemPaper',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('paper_id', models.CharField(max_length=100, null=True, db_index=True)),
                ('problem_id', models.IntegerField(verbose_name='\u9898\u7801', db_index=True)),
                ('exam_selected', models.CharField(blank=True, max_length=10, verbose_name='\u7b54\u9898\u4eba\u9009\u9879', choices=[(b'A', 'A'), (b'B', 'B'), (b'C', 'C'), (b'D', 'D')])),
                ('exam_answer', models.CharField(max_length=10, verbose_name='\u6b63\u786e\u9009\u9879', blank=True)),
                ('exam_problem_score', models.IntegerField(null=True, verbose_name='\u9898\u76ee\u5206\u6570', db_index=True)),
                ('examproblemselects', models.ManyToManyField(to='examination.ExamProblemSelect')),
                ('user', models.ForeignKey(default=None, verbose_name='\u7b54\u9898\u4eba', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'db_table': 'shop_examination_paper_select_problem',
                'verbose_name': '\u8003\u8bd5\u5377\u4fe1\u606f',
                'verbose_name_plural': '\u8003\u8bd5\u5377\u4fe1\u606f\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='ExamUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('exam_grade', models.IntegerField(default=0, verbose_name='\u8003\u8bd5\u5f97\u5206')),
                ('paper_id', models.CharField(max_length=100, verbose_name='\u5377', blank=True)),
                ('exam_selected_num', models.IntegerField(null=True, verbose_name='\u7b54\u9898\u4eba\u7b54\u9898\u6570', db_index=True)),
                ('exam_date', models.DateTimeField(auto_now_add=True, verbose_name=b'\xe7\xad\x94\xe9\xa2\x98\xe6\x97\xa5\xe6\x9c\x9f', null=True)),
                ('user', models.ForeignKey(default=None, verbose_name='\u7b54\u9898\u4eba', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'db_table': 'shop_examination_user',
                'verbose_name': '\u8003\u8bd5\u7528\u6237\u4fe1\u606f',
                'verbose_name_plural': '\u8003\u8bd5\u7528\u6237\u4fe1\u606f\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='ExmaEssayQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('exam_problem', models.CharField(max_length=1500, verbose_name='\u9898\u76ee', blank=True)),
                ('exam_selected', models.CharField(max_length=6000, verbose_name='\u7b54\u9898\u4eba\u9009\u9879', blank=True)),
                ('exam_answer', models.CharField(max_length=6000, verbose_name='\u9009\u9879', blank=True)),
                ('exam_problem_score', models.IntegerField(default=2, null=True, verbose_name='\u9898\u76ee\u5206\u6570', db_index=True)),
                ('exam_problem_created', models.DateTimeField(null=True, verbose_name='\u521b\u5efa\u65e5\u671f', blank=True)),
            ],
            options={
                'db_table': 'shop_examination_essay_question',
                'verbose_name': '\u8003\u8bd5wenda\u9898\u5e93',
                'verbose_name_plural': '\u8003\u8bd5wenda\u9898\u5e93\u5217\u8868',
            },
        ),
        migrations.AddField(
            model_name='examessayquestionpaper',
            name='examessayquestion',
            field=models.ManyToManyField(to='examination.ExmaEssayQuestion'),
        ),
        migrations.AddField(
            model_name='examessayquestionpaper',
            name='user',
            field=models.ForeignKey(default=None, verbose_name='\u7b54\u9898\u4eba', to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='examselectproblempaper',
            unique_together=set([('user', 'problem_id', 'paper_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='examessayquestionpaper',
            unique_together=set([('user', 'problem_id', 'paper_id')]),
        ),
    ]
