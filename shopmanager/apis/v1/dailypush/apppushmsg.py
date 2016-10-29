# coding=utf-8
__ALL__ = [
    'get_app_push_msg_by_id',
    'get_minutes_failed_msgs',
    'push_app_push_msg_2_client_by_id',
    'push_msg_right_now_by_id',
    'delete_app_push_msg',
]
import datetime
import logging

logger = logging.getLogger(__name__)


def _validate_record(k, v):
    # type: (text_type, Any) -> None
    """校验选择项参数
    """
    from flashsale.protocol.models import APPFullPushMessge

    def test_platform(v):
        if v not in dict(APPFullPushMessge.PLATFORM_CHOICES).keys():
            raise Exception(u'推送设备平台选择错误!')

    def test_push_time(v):
        if v < datetime.datetime.now():
            raise Exception(u'推送时间应该大于当前时间!')

    def test_target_url(v):
        if v not in dict(APPFullPushMessge.TARGET_CHOICES).keys():
            raise Exception(u'推送的跳转页面设置错误!')

    key_map = {
        'platform': test_platform,
        'push_time': test_push_time,
        'target_url': test_target_url,
    }
    if k in key_map.keys():
        return key_map[k](v)


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


def push_app_push_msg_2_client_by_id(id):
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


def create_app_push_msg(desc, platform, push_time, **kwargs):
    # type: (text_type, text_type, datetime.datetime, **Any) -> APPFullPushMessge
    from flashsale.protocol.models import APPFullPushMessge

    target_url = kwargs.get('target_url') or 1
    params_url = kwargs.get('params_url') or {}
    _validate_record('target_url', target_url)
    _validate_record('params_url', params_url)
    _validate_record('push_time', push_time)

    msg = APPFullPushMessge(desc=desc,
                            target_url=target_url,
                            platform=platform,
                            push_time=push_time,
                            params={'url': params_url})
    msg.save()
    return msg


def delete_app_push_msg_by_id(id):
    # type: (int) -> bool
    from flashsale.protocol.models import APPFullPushMessge

    app_push = get_app_push_msg_by_id(id)
    if app_push.status == APPFullPushMessge.SUCCESS:
        raise Exception(u'推送生效的记录不予删除!')
    app_push.delete()
    return True


def update_app_push_msg_by_id(id, **kwargs):
    # type(int, **Any) -> APPFullPushMessge
    app_push = get_app_push_msg_by_id(id)
    if kwargs.has_key('params_url'):  # 不更新传入的turns_num
        params_url = kwargs.pop('params_url')
        app_push.params.update({'url': params_url})
    for k, v in kwargs.iteritems():
        if hasattr(app_push, k) and getattr(app_push, k) != v:
            _validate_record(k, v)
            setattr(app_push, k, v)
    app_push.save()
    return app_push


class AppPushMessge(object):
    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.desc = kwargs['desc']
        self.target_url = 1
        self.params = {}
        self.cat = 0
        self.platform = kwargs['platform']
        self.regid = ''
        self.result = {}
        self.status = 0
        self.push_time = kwargs['push_time']
