# coding=utf-8
from __future__ import absolute_import, unicode_literals
import datetime
from core.managers import BaseManager


class OrderShareCouponManager(BaseManager):
    def create_coupon_share(self, tpl, customer, uniq_id, ufrom, **kwargs):
        share = self.filter(share_customer=customer.id, template_id=tpl.id, uniq_id=uniq_id).first()
        # step 1 : search this customer share uniq_id , if exist return it an log the share uform info
        # update the status if the time is end
        if share:
            now = datetime.datetime.now()
            if now > share.share_end_time:
                share.status = self.model.FINISHED
                share.save(update_fields=['status'])

            platform_info = share.platform_info
            if isinstance(platform_info, str):
                platform_info = eval(share.platform_info)

            if platform_info.has_key(ufrom):  # 如果有则增加数量
                platform_info[ufrom] += 1
            else:
                platform_info[ufrom] = 1
            share.platform_info = platform_info
            share.save(update_fields=['platform_info'])
            return False, share
        else:
            # step 2 : if not exist to create one an return it.
            extras = {
                'user_info':
                    {'id': customer.id, 'nick': customer.nick, 'thumbnail': customer.thumbnail},
                'templates':
                    {'post_img': tpl.post_img,
                     'title': tpl.title,
                     'description': tpl.description}  # 优惠券模板
            }
            value, start_use_time, expires_time = tpl.calculate_value_and_time()
            order_share = self.create(
                template_id=tpl.id,
                share_customer=customer.id,
                uniq_id=uniq_id,

                limit_share_count=tpl.share_times_limit,
                platform_info={ufrom: 1},
                share_start_time=start_use_time,
                share_end_time=expires_time,
                extras=extras,
            )
            return True, order_share
