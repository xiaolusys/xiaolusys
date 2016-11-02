# -*- coding: utf-8 -*-
from django.contrib import admin
from shopapp.examination.models import ExamProblemSelect, ExamSelectProblemPaper, ExamUser, ExmaEssayQuestion, \
    ExamEssayQuestionPaper


class ExamAdmin(admin.ModelAdmin):
    list_display = ('exam_problem', 'exam_answer', 'option_a', 'option_b', 'option_c', 'option_d', 'exam_problem_score',
                    'exam_problem_created')


admin.site.register(ExamProblemSelect, ExamAdmin)


class ExamPaperAdmin(admin.ModelAdmin):
    list_display = ('user', 'paper_id', 'problem_id', 'exam_selected', 'exam_answer', 'exam_problem_score',)


admin.site.register(ExamSelectProblemPaper, ExamPaperAdmin)


class ExamUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'paper_id', 'exam_grade', 'exam_selected_num', 'exam_date',)


admin.site.register(ExamUser, ExamUserAdmin)


class ExamEssayQuestionAdmin(admin.ModelAdmin):
    list_display = ('exam_problem', 'exam_answer', 'exam_problem_score', 'exam_problem_created')


admin.site.register(ExmaEssayQuestion, ExamEssayQuestionAdmin)


class ExmaEssayQuestionPaperAdmin(admin.ModelAdmin):
    list_display = ('paper_id', 'user', 'problem_id', 'exam_selected', 'exam_problem_score')


admin.site.register(ExamEssayQuestionPaper, ExmaEssayQuestionPaperAdmin)
