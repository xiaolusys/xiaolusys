# coding=utf-8
import datetime
from celery import task
from flashsale.protocol import get_target_url
from flashsale.protocol.models import APPFullPushMessge
from flashsale.xiaolumm import util_emoji
from flashsale.push.app_push import AppPush

import logging

log = logging.getLogger(__name__)


def sit_push(obj, now):
    resp = {}

    if now < obj.push_time:
        return

    target_url = get_target_url(obj.target_url, obj.params)
    msg = util_emoji.match_emoji(obj.desc)  # 生成推送内容

    if obj.platform == APPFullPushMessge.PL_ALL:
        resp = AppPush.push_to_all(target_url, msg)

    if obj.platform in [APPFullPushMessge.PL_IOS, APPFullPushMessge.PL_ANDROID]:
        resp = AppPush.push_to_platform(obj.platform, target_url, msg)
    else:
        resp = AppPush.push_to_topic(obj.platform, target_url, msg)

    obj.result = resp
    success = resp.get('android', {}).get('result', None) or resp.get('ios', {}).get('result', None)
    if success and success.lower() == 'ok':
        obj.status = APPFullPushMessge.SUCCESS  # 保存推送成功状态
    obj.save()


@task
def task_site_push(obj=None):
    """
    定时周期性任务
    每半个小时执行一次检查
    如果有半个小时内的推送设置记录（未推送状态的）
    全站点推送该条记录
    """
    now = datetime.datetime.now()
    if obj:
        sit_push(obj, now)  # admin 后台手动执行
        log.warn('site_push:%s.' % obj.id)
    else:  # 定时任务执行
        thirth_minute_ago = now - datetime.timedelta(minutes=30)  # 30分钟之前的时间

        allpushsmss = APPFullPushMessge.objects.filter(push_time__gte=thirth_minute_ago, push_time__lt=now,
                                                       status=APPFullPushMessge.FAIL).order_by('-push_time')
        log.warn('site push time_zone : %s-%s' % (thirth_minute_ago, now))
        for obj in allpushsmss:
            sit_push(obj, now)
