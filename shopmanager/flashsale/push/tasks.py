# coding: utf-8

from celery.task import task

from .mipush import mipush_of_ios, mipush_of_android

@task(max_retry=3, default_retry_delay=5)
def subscribe(platform, regid, topic):
    mipush_instance = mipush_of_ios if platform == 'ios' else mipush_of_android
    mipush_instance.subscribe_by_regid(regid, topic)

@task(max_retry=3, default_retry_delay=5)
def unsubscribe(platform, regid, topic):
    mipush_instance = mipush_of_ios if platform == 'ios' else mipush_of_android
    mipush_instance.unsubscribe_by_regid(regid, topic)
