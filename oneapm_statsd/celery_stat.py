from __future__ import absolute_import

from django_statsd.clients import statsd

def on_task_sent_count(sender=None, task_id=None, task=None, **kwds):
    """
    Handle Celery ``task_sent`` signals.
    """
    # Increase statsd counter.
    statsd.incr('celery.total_send_count')


def on_task_prerun_count(sender=None, task_id=None, task=None, **kwds):
    """
    Handle Celery ``task_prerun``signals.
    """
    # Increase statsd counter.
    statsd.incr('celery.total_prerun_count')


def on_task_postrun_count(sender=None, task_id=None, task=None, **kwds):
    """
    Handle Celery ``task_postrun`` signals.
    """
    # Increase statsd counter.
    statsd.incr('celery.total_postrun_count')


def on_task_failure_count(sender=None, task_id=None, task=None, **kwds):
    """
    Handle Celery ``task_failure`` signals.
    """
    # Increase statsd counter.
    statsd.incr('celery.total_failure_count')


def register_celery_events():
    pass
    # new celery version not support well
    # try:
    #     from celery import signals
    # except ImportError:
    #     pass
    # else:
    #     signals.task_sent.connect(on_task_sent_count)
    #     signals.task_prerun.connect(on_task_prerun_count)
    #     signals.task_postrun.connect(on_task_postrun_count)
    #     signals.task_failure.connect(on_task_failure_count)