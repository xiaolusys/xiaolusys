from django.contrib import admin
from flashsale.mmexam.models import Question, Choice, Result, MamaDressResult, DressProduct, Mamaexam, ExamResultDetail


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


class Qestiondmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'question_types', 'start_time', 'real_answer')
    ordering = ['id']
    list_filter = ['start_time']
    inlines = [ChoiceInline]


class Choicedmin(admin.ModelAdmin):
    list_display = ('question', 'choice_title', 'choice_text',)


class Resultdmin(admin.ModelAdmin):
    search_fields = ['daili_user', 'xlmm_id', 'customer_id']
    list_display = ('customer_id', 'xlmm_id', 'daili_user', 'total_point', 'exam_state', 'sheaves', 'exam_date',
                    'modified')
    list_filter = ['exam_state', 'sheaves', 'exam_date', 'created', 'modified']

class Mamaexamdmin(admin.ModelAdmin):
    list_display = (
        "sheaves",
        "start_time",
        "expire_time",
        "valid",
        "extras"
    )


admin.site.register(Mamaexam, Mamaexamdmin)
admin.site.register(Question, Qestiondmin)
admin.site.register(Choice, Choicedmin)
admin.site.register(Result, Resultdmin)


class MamaDressResultAdmin(admin.ModelAdmin):
    list_display = ('user_unionid', 'mama_nick', 'exam_score', 'exam_date', 'exam_state')
    search_fields = ['=user_unionid', '=referal_from']


admin.site.register(MamaDressResult, MamaDressResultAdmin)


class DressProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'age_min', 'age_max', 'category', 'product_id', 'modified', 'in_active')
    search_fields = ['=product_id']

    list_filter = ['in_active', 'created', 'category']


admin.site.register(DressProduct, DressProductAdmin)


class ExamResultDetailAdmin(admin.ModelAdmin):
    list_display = (
        "customer_id",
        "sheaves",
        "question_id",
        "answer",
        "is_right",
        "point",
    )
    search_fields = ['=customer_id', '=question_id']

    list_filter = ['sheaves', 'created']


admin.site.register(ExamResultDetail, ExamResultDetailAdmin)
