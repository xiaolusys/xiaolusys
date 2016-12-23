from __future__ import absolute_import

from django_statsd.clients import statsd

def on_before_task_publish_count(sender=None, task_id=None, task=None, **kwds):
    """
    Handle Celery ``task_sent`` signals.
    """
    # Increase statsd counter.
    statsd.incr('celery.count.before_publish')


def on_after_task_publish_count(sender=None, task_id=None, task=None, **kwds):
    """
    Handle Celery ``task_sent`` signals.
    """
    # Increase statsd counter.
    statsd.incr('celery.count.after_publish')


def on_task_prerun_count(sender=None, task_id=None, task=None, **kwds):
    """
    Handle Celery ``task_prerun``signals.
    """
    # Increase statsd counter.
    statsd.incr('celery.count.prerun')


def on_task_postrun_count(sender=None, task_id=None, task=None, **kwds):
    """
    Handle Celery ``task_postrun`` signals.
    """
    # Increase statsd counter.
    statsd.incr('celery.count.postrun')


def on_task_success_count(sender=None, task_id=None, task=None, **kwds):
    """
    Handle Celery ``task_sent`` signals.
    """
    # Increase statsd counter.
    statsd.incr('celery.count.success')


def on_task_failure_count(sender=None, task_id=None, task=None, **kwds):
    """
    Handle Celery ``task_failure`` signals.
    """
    # Increase statsd counter.
    statsd.incr('celery.count.failure')

def on_task_retry_count(sender=None, task_id=None, task=None, **kwds):
    """
    Handle Celery ``task_postrun`` signals.
    """
    # Increase statsd counter.
    statsd.incr('celery.count.retry')


def on_task_revoked_count(sender=None, task_id=None, task=None, **kwds):
    """
    Handle Celery ``task_sent`` signals.
    """
    # Increase statsd counter.
    statsd.incr('celery.count.revoked')

def on_task_unknown_count(sender=None, task_id=None, task=None, **kwds):
    """
    Handle Celery ``task_failure`` signals.
    """
    # Increase statsd counter.
    statsd.incr('celery.count.unknown')


def on_task_rejected_count(sender=None, task_id=None, task=None, **kwds):
    """
    Handle Celery ``task_failure`` signals.
    """
    # Increase statsd counter.
    statsd.incr('celery.count.rejected')


def register_celery_events():
    # new celery version not support well
    try:
        from celery import signals
    except ImportError:
        pass
    else:
        signals.before_task_publish.connect(on_before_task_publish_count)
        signals.after_task_publish.connect(on_after_task_publish_count)
        signals.task_prerun.connect(on_task_prerun_count)
        signals.task_postrun.connect(on_task_postrun_count)
        signals.task_success.connect(on_task_success_count)
        signals.task_failure.connect(on_task_failure_count)
        signals.task_retry.connect(on_task_retry_count)
        signals.task_revoked.connect(on_task_revoked_count)
        signals.task_unknown.connect(on_task_unknown_count)
        signals.task_rejected.connect(on_task_rejected_count)