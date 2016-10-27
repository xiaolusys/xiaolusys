# coding=utf-8
from celery import task
import logging

log = logging.getLogger(__name__)


@task
def task_site_push(id=None):
    # type: (Optional[int]) -> None
    """如果有半个小时内的推送设置记录（未推送状态的）　则　执行推送该消息给客户端程序
    """
    from apis.v1.dailypush.apppushmsg import app_msg_push_2_client_by_id, get_minutes_failed_msgs
    if id:
        app_msg_push_2_client_by_id(id)
    else:
        for obj in get_minutes_failed_msgs():
            app_msg_push_2_client_by_id(obj.id)
