# -*- coding:utf8 -*-
"""
@author: meixqhi
@since: 2014-02-18 
"""
from datetime import datetime, timedelta
import time
import json
from celery.task import task
from celery.task.sets import subtask
from celery import Task
from shopapp.comments.models import Comment, CommentItem
from common.utils import single_instance_task

import logging

CRAW_LAST_DAYS = 14  # 初次抓取评论的天数
COMMENT_MIN_LEN = 5  # 评论最少字数
logger = logging.getLogger('celery.handler')


class CrawItemCommentTask(Task):
    """ 抓取在售商品评论 """

    def __init__(self):
        self.item = None

    def get_total_results(self, response):
        return response.get('total_results', None)

    def get_trade_rates(self, response):
        if not response.has_key('trade_rates'):
            return []
        return response['trade_rates']['trade_rate']

    def get_has_next(self, response):
        return response.get('has_next', None)

    def handle_response(self, response):

        from shopback.orders.models import Order
        for rate in self.get_trade_rates(response):
            if len(rate.get('content', '')) < COMMENT_MIN_LEN:
                continue

            comment, state = Comment.objects.get_or_create(
                num_iid=rate['num_iid'],
                tid=rate['tid'],
                oid=rate['oid'],
                role=rate['role'])

            for k, v in rate.iteritems():
                hasattr(comment, k) and setattr(comment, k, v)

            if comment.reply:
                comment.is_reply = True

            orders = Order.objects.filter(oid=rate['oid'])
            if orders.count():
                comment.item_title = comment.item_title + u'\u3010%s\u3011' % orders[0].sku_properties_name
            comment.item_pic_url = self.item.pic_url
            comment.detail_url = self.item.detail_url
            comment.ignored = False
            comment.save()

    def run(self, num_iid):

        try:
            from auth import apis
            from shopback.items.models import Item

            self.item = Item.objects.get(num_iid=num_iid)
            comment_item, state = CommentItem.objects.get_or_create(num_iid=num_iid)

            dt = datetime.now()
            if not comment_item.updated:
                comment_item.updated = dt - timedelta(days=CRAW_LAST_DAYS)

            if not comment_item.is_active:
                return False

            page_no = 0
            has_next = True
            while has_next:
                response = apis.taobao_traderates_get(rate_type='get',
                                                      role='buyer',
                                                      num_iid=num_iid,
                                                      page_no=page_no,
                                                      page_size=100,
                                                      start_date=comment_item.updated,
                                                      end_date=dt,
                                                      use_has_next=True,
                                                      tb_user_id=self.item.user.visitor_id)

                response = response['traderates_get_response']
                self.handle_response(response)
                has_next = self.get_has_next(response)
                page_no += 1

            comment_item.updated = dt
            comment_item.title = self.item.title
            comment_item.pic_url = self.item.pic_url
            comment_item.detail_url = self.item.detail_url
            comment_item.save()

        except Exception, exc:
            logger.error(exc.message or str(exc), exc_info=True)


@single_instance_task(3 * 60 * 60, prefix='shopapp.comments.tasks.')
def crawAllUserOnsaleItemComment():
    from shopback.users.models import User
    from shopback.items.models import Item
    from shopback import paramconfig as pcfg

    users = User.effect_users.all()

    onsale_items = Item.objects.filter(user__in=users, approve_status=pcfg.ONSALE_STATUS)

    for item in onsale_items:
        CrawItemCommentTask().delay(item.num_iid)
