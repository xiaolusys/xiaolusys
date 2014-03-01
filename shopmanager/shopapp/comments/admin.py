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
from shopback.base.options import DateFieldListFilter

class CommentAdmin(admin.ModelAdmin):
    
    list_display = ('id','item_image_link','content_link','result','tid','nick','rated_nick','created','explain_link')
    
    ordering = ['-created']
    
    list_filter = ('is_reply','ignored','result','valid_score',('replay_at',DateFieldListFilter))
    search_fields = ['num_iid','tid', 'oid', 'content','replayer__username']
    
    def content_link(self, obj):
        return (u'<div style="display:inline-block;"><a href="javascript:void(0);" class="btn btn-small %s" cid="%d">%s</a>'
                %(('','btn-info')[0 if obj.ignored else 1],obj.id,(u'忽略',u'已忽略')[1 if obj.ignored else 0])+
                '</div><div class="well well-large">%s</div>'%(obj.content))
    
    content_link.allow_tags = True
    content_link.short_description = "评价内容"
    
    def item_image_link(self, obj):
        return (u'<a href="%s" target="_blank"><img src="%s"  title="%s" width="80px" height="60px"/></a>'%(obj.detail_url,obj.item_pic_url,obj.item_title))
    
    item_image_link.allow_tags = True
    item_image_link.short_description = "商品图片"
    
    def explain_link(self, obj):
        return (u'<a href="javascript:void(0);" class="btn %s" cid="%d" nick="%s">%s</a>'%
                (('','btn-success')[0 if obj.is_reply else 1],obj.id,obj.nick,(u'解释',u'已回复')[1 if obj.is_reply else 0]))
    
    explain_link.allow_tags = True
    explain_link.short_description = "解释评价"
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'16'})},
        models.FloatField: {'widget': TextInput(attrs={'size':'16'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }
    
    class Media:
        css = {"all": ("admin/css/forms.css","css/admin/dialog.css","css/admin/common.css","jquery/jquery-ui-1.10.1.css")}
        js = ("jquery/jquery-ui-1.8.13.min.js","jquery/addons/jquery.form.js","script/admin/adminpopup.js","comments/js/comment.js")

admin.site.register(Comment, CommentAdmin)  


class CommentItemAdmin(admin.ModelAdmin):
    
    list_display = ('num_iid','title','updated','is_active')
    
    ordering = ['-updated']
    
    list_filter = ('is_active',)
    search_fields = ['num_iid','title']
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'16'})},
        models.FloatField: {'widget': TextInput(attrs={'size':'16'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }

admin.site.register(CommentItem, CommentItemAdmin)      


