from django.contrib import admin
from flashsale.mmexam.models import Question,Choice,Result

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    
class Qestiondmin(admin.ModelAdmin):
    
    list_display = ('id','question','single_many', 'pub_date', 'real_answer')
    ordering=['id']
    inlines = [ChoiceInline]
    list_filter = ['pub_date']
    
class Choicedmin(admin.ModelAdmin):
    
    list_display = ('question', 'choice_title','choice_text', )
    
class Resultdmin(admin.ModelAdmin):
    search_fields = ['daili_user']
    list_display = ('daili_user', 'exam_state','exam_date', )    
admin.site.register(Question,Qestiondmin)

admin.site.register(Choice,Choicedmin)
admin.site.register(Result,Resultdmin)