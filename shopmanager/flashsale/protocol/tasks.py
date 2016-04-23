# coding=utf-8
__author__ = 'jishu_linjie'
import datetime
from celery import task
from flashsale.push import mipush
from flashsale.protocol import get_target_url
from flashsale.protocol.models import APPFullPushMessge
from flashsale.xiaolumm import util_emoji

import logging

log = logging.getLogger(__name__)


def sit_push(obj, now):
    resp = {}
    if obj.platform == APPFullPushMessge.PL_IOS and now > obj.push_time:  # 执行推送时间必须在设定的执行时间之后
        params = {'target_url': get_target_url(obj.target_url, obj.params)}
        desc = util_emoji.match_emoji(obj.desc)  # 生成推送内容

        resp = mipush.mipush_of_ios.push_to_all(params, description=desc)  # 推送
        obj.result = resp  # 保存推送结果

    if obj.platform == APPFullPushMessge.PL_ANDROID and now > obj.push_time:
        params = {'target_url': get_target_url(obj.target_url, obj.params)}
        desc = util_emoji.match_emoji(obj.desc)

        resp = mipush.mipush_of_android.push_to_all(params, description=desc)
        obj.result = resp

    success = resp.get('result')
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

