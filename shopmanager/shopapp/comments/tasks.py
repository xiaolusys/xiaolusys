#-*- coding:utf8 -*-
"""
@author: meixqhi
@since: 2014-02-18 
"""
from datetime import datetime,timedelta
import time
import json
from shopback import paramconfig as pcfg
from celery.task import task
from celery.task.sets import subtask
from celery import Task
import logging

CRAW_LAST_DAYS = 14
logger = logging.getLogger('celery.handler')


class CrawItemCommentTask(Task):
    """ 抓取所有在售商品评论 """
            
    def get_total_results(self,response):    
        return response['traderates_get_response'].get('total_results',0)
    
    def get_trade_rates(self,response):
        if self.get_total_results(response)>0:
            return response['traderates_get_response']['trade_rates']['trade_rate']
        return []
        
    def get_has_next(self,response):
        return response['traderates_get_response'].get('has_next',False)   
    
    def handle_response(self,response):
        
        for rate in self.get_trade_rates(response):
            
            comment,state = Comment.objects.get_or_create(
                                                    num_iid=rate['num_iid'],
                                                    tid=rate['tid'],
                                                    oid=rate['oid'],
                                                    role=rate['role'])
            
            for k,v in rate.iteritems():
                hasattr(comment,k) and setattr(comment,k,v)
                
            if comment.reply:
                comment.is_reply = True
            
            comment.ignored = False
            comment.save()
                
            
    def run(self,num_iid):
        
        try:
            from auth import apis
            from shopback.items.models import Item
            from shopapp.comments.models import Comment,CommentItem
            
            item  = Item.objects.get(num_iid=num_iid)
            comment_item,state = CommentItem.objects.get_or_create(num_iid=num_iid)
            
            dt = datetime.now()
            if not comment_item.updated:
                comment_item.updated = dt - timedelta(days=CRAW_LAST_DAYS)
                
            if not comment_item.is_active:
                return False
            
            page_no   = 0
            has_next  = True
            while has_next:
                response = apis.taobao_traderates_get(rate_type='get',
                                                      role='buyer',
                                                      num_iid=num_iid,
                                                      page_no=page_no,
                                                      page_size=100,
                                                      start_date=comment_item.updated,
                                                      end_date=dt,
                                                      use_has_next=True,
                                                      tb_user_id=item.user.visitor_id)
                
                self.handle_response(response)
                has_next  = self.get_has_next(response)
                page_no   += 1
            
            comment_item.title   = item.title
            comment_item.pic_url = item.pic_url
            comment_item.save()
            
        except Exception,exc:
            logger.error(exc.message or str(exc),exc_info=True)
        
                
        
    
    
@task
def crawAllUserOnsaleItemComment():
    
    from shopback.users.models import User
    from shopback.items.models import Item
    
    users  = User.objects.filter(status=pcfg.NORMAL)
    
    onsale_items = Item.objects.filter(user__in=users,approve_status=pcfg.ONSALE_STATUS)
        
    for item in onsale_items:
        CrawItemCommentTask().delay(item.num_iid)
    
    
    

