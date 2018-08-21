# -*- coding: utf-8 -*-
from django.contrib import admin
from shopapp.weixin_examination.models import (ExamProblem,
                                               ExamPaper,
                                               ExamUserPaper,
                                               ExamUserProblem,
                                               Invitationship)


class ExamProblemAdmin(admin.ModelAdmin):
    list_display = ('id', 'problem_title', 'problem_answer', 'problem_score', 'created', 'status')
    list_display_links = ('id', 'problem_title')

    list_filter = ('status', 'problem_answer')
    search_fields = ['id', 'problem_title']


admin.site.register(ExamProblem, ExamProblemAdmin)


class ExamPaperAdmin(admin.ModelAdmin):
    list_display = ('id', 'paper_title', 'problem_num', 'modified', 'created', 'status')
    list_display_links = ('id', 'paper_title')

    list_filter = ('status',)
    search_fields = ['id', 'paper_title']


admin.site.register(ExamPaper, ExamPaperAdmin)


class ExamUserPaperAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_openid', 'paper_id', 'answer_num', 'grade', 'modified', 'created', 'status')
    list_display_links = ('id', 'user_openid')

    list_filter = ('status',)
    search_fields = ['id', 'user_openid', 'paper_id']


admin.site.register(ExamUserPaper, ExamUserPaperAdmin)


class ExamUserProblemAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_openid', 'paper_id', 'problem_id', 'selected', 'problem_score', 'created', 'status')
    list_display_links = ('id', 'user_openid')

    list_filter = ('status',)
    search_fields = ['id', 'user_openid', 'paper_id', 'problem_id']


admin.site.register(ExamUserProblem, ExamUserProblemAdmin)


class InvitationshipAdmin(admin.ModelAdmin):
    list_display = ('from_openid', 'invite_openid', 'created')
    list_display_links = ('from_openid',)

    search_fields = ['from_openid', 'invite_openid']


admin.site.register(Invitationship, InvitationshipAdmin)
