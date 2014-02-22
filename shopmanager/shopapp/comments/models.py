#-*- coding:utf-8 -*-
"""
@author: meixqhi
@since: 2014-02-18 
"""
from django.db import models
from shopback.base.fields import BigIntegerAutoField

ROLE_CHOICES = (
                ('seller',u'卖家'),
                ('buyer',u'买家')
                )

RESULT_CHOICES = (
                ('good',u'好评'),
                ('neutral',u'中评'),
                ('bad',u'差评'),
                )

class Comment(models.Model):
    
    id = BigIntegerAutoField(primary_key=True)
    
    num_iid = models.BigIntegerField(null=False,db_index=True,verbose_name=u'商品ID')
    tid     = models.BigIntegerField(null=False,db_index=True,verbose_name=u'交易ID')
    oid     = models.BigIntegerField(null=False,db_index=True,verbose_name=u'订单ID')
    
    item_title  = models.CharField(max_length=148,blank=True,verbose_name=u'商品标题')
    item_pic_url = models.URLField(verify_exists=False,blank=True,verbose_name=u'商品图片')
    detail_url   = models.URLField(verify_exists=False,blank=True,verbose_name=u'详情链接')
    item_price  = models.DecimalField(max_digits=10,null=True,decimal_places=2,verbose_name=u'商品价格')
    
    valid_score = models.BooleanField(default=True,verbose_name=u'是否记分')
    role    = models.CharField(max_length=8,choices=ROLE_CHOICES,verbose_name=u'角色')
    result  = models.CharField(max_length=8,blank=True,choices=RESULT_CHOICES,verbose_name=u'评价结果')
    
    nick    = models.CharField(max_length=32,blank=True,verbose_name=u'评价者昵称')
    rated_nick = models.CharField(max_length=32,blank=True,verbose_name=u'被评价者昵称')
    
    content = models.CharField(max_length=1500,blank=True,verbose_name=u'评价内容')
    reply   = models.CharField(max_length=1500,blank=True,verbose_name=u'评价解释')
    
    is_reply = models.BooleanField(default=False,verbose_name=u'已回复')
    ignored  = models.BooleanField(default=False,verbose_name=u'已忽略')
    
    created = models.DateTimeField(blank=True,null=True,verbose_name=u'创建日期')
    
    class Meta:
        db_table = 'shop_comments_comment'
        unique_together = ('num_iid', 'tid', 'oid', 'role')
        verbose_name = u'交易评论'
        verbose_name_plural = u'交易评论列表'
        
    def reply_order_comment(self,content):
    
        from auth import apis
        from shopback.items.models import Item
        
        rel_item = Item.objects.get(num_iid=self.num_iid)
        
        res = apis.taobao_traderate_explain_add(oid=self.oid,
                                                reply=content,
                                                tb_user_id=rel_item.user.visitor_id)
        if not res['traderate_explain_add_response']['is_success']:
            raise Exception('解释失败！')
        
        self.reply = content
        self.is_reply = True
        self.save()
        
        
class CommentItem(models.Model):
    
    num_iid  = models.BigIntegerField(primary_key=True,verbose_name=u'商品ID')
    
    title    = models.CharField(max_length=64,blank=True,verbose_name=u'标题')
    pic_url = models.URLField(verify_exists=False,blank=True,verbose_name=u'商品图片')
    detail_url   = models.URLField(verify_exists=False,blank=True,verbose_name=u'详情链接')
    
    updated  = models.DateTimeField(blank=True,null=True,verbose_name=u'更新日期')
    is_active = models.BooleanField(default=True,verbose_name=u'有效')
    
    class Meta:
        db_table = 'shop_comments_commentitem'
        verbose_name = u'评价商品'
        verbose_name_plural = u'评价商品列表'
        
        
        