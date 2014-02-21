#-*- coding:utf8 -*-
"""
@author: meixqhi
@since: 2014-02-18 
"""
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from django.http import HttpResponse
from shopapp.comments.models import Comment,CommentItem

class CommentAdmin(admin.ModelAdmin):
    
    list_display = ('num_iid','content','result','nick','rated_nick','is_reply','created')
    
    date_hierarchy = '-created'
    
    list_filter = ('is_reply','ignored','role','result','is_reply','valid_score')
    search_fields = ['num_iid','tid', 'oid']
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'16'})},
        models.FloatField: {'widget': TextInput(attrs={'size':'16'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }

admin.site.register(Comment, CommentAdmin)  


class CommentItemAdmin(admin.ModelAdmin):
    
    list_display = ('num_iid','title','updated','is_active')
    
    date_hierarchy = '-updated'
    
    list_filter = ('is_active',)
    search_fields = ['num_iid','title']
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'16'})},
        models.FloatField: {'widget': TextInput(attrs={'size':'16'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }

admin.site.register(CommentItem, CommentItemAdmin)      


