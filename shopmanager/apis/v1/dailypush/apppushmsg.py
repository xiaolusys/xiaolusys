# coding=utf-8
__ALL__ = [
    'get_app_push_msg_by_id',
    'get_minutes_failed_msgs',
    'app_msg_push_2_client_by_id',
]
import datetime
import logging

logger = logging.getLogger(__name__)


def get_app_push_msg_by_id(id):
    # type: (int) -> APPFullPushMessge
    from flashsale.protocol.models import APPFullPushMessge

    return APPFullPushMessge.objects.get(id=id)


def get_minutes_failed_msgs(minutes=30):
    # type: (int) -> List[APPFullPushMessge]
    """指定（默认30）分钟内推送失败的（没有推送成功的）推送记录
    """
    from flashsale.protocol.models import APPFullPushMessge

    now = datetime.datetime.now()
    thirth_minute_ago = now - datetime.timedelta(minutes=minutes)  # 30分钟之前的时间 failed msg
    allpushsmss = APPFullPushMessge.objects.filter(push_time__gte=thirth_minute_ago,
                                                   push_time__lt=now,
                                                   status=APPFullPushMessge.FAIL).order_by('-push_time')
    return allpushsmss


def app_msg_push_2_client_by_id(id):
    # type: (int) -> None
    """推送消息给客户端
    """
    from flashsale.protocol import get_target_url
    from flashsale.xiaolumm import util_emoji
    from flashsale.push.app_push import AppPush
    from flashsale.protocol.models import APPFullPushMessge

    now = datetime.datetime.now()
    push_msg = get_app_push_msg_by_id(id)
    if now < push_msg.push_time:  # 定义的推送时间　没有到　则不推送
        return
    raise Exception(u'上线去掉!')
    target_url = get_target_url(push_msg.target_url, push_msg.params)
    msg = util_emoji.match_emoji(push_msg.desc)  # 生成推送内容

    if push_msg.platform == APPFullPushMessge.PL_ALL:
        resp = AppPush.push_to_all(target_url, msg)
    elif push_msg.platform in [APPFullPushMessge.PL_IOS, APPFullPushMessge.PL_ANDROID]:
        resp = AppPush.push_to_platform(push_msg.platform, target_url, msg)
    else:
        resp = AppPush.push_to_topic(push_msg.platform, target_url, msg)

    push_msg.result = resp
    success = resp.get('android', {}).get('result', None) or resp.get('ios', {}).get('result', None)
    if success and success.lower() == 'ok':
        push_msg.status = APPFullPushMessge.SUCCESS  # 保存推送成功状态
    push_msg.save(update_fields=['status', 'modified'])

    logger.info({
        'action': 'dailypush.app_msg_push_2_client_by_id',
        'msg_id': id
    })


def push_msg_right_now_by_id(id):
    # type: (id, Optional[int]) -> bool
    """执行则立即推送（执行task）
    """
    from flashsale.protocol.tasks import task_site_push
    from flashsale.protocol.models import APPFullPushMessge

    push_msg = get_app_push_msg_by_id(id)
    if not push_msg.push_time or push_msg.status == APPFullPushMessge.SUCCESS:
        return False
    try:
        task_site_push.delay(push_msg.id)
    except Exception, exc:
        resp = {'error': exc.message}
        push_msg.result = resp
        push_msg.save(update_fields=['result', 'modified'])
        return False
    return True


class AppPushMessge(object):
    def __init__(self, **kwargs):
        self.desc = kwargs['desc']
        self.target_url = 1
        self.params = {}
        self.cat = 0
        self.platform = kwargs['platform']
        self.regid = kwargs['regid']
        self.result = {}
        self.status = 0
        self.push_time = kwargs['push_time']