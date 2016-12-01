# coding=utf-8
import os
from .production import *

DEBUG = False

INSTALLED_APPS.extend([
    'django_prometheus',
])

##########################SENTRY RAVEN##########################
import raven
RAVEN_CONFIG = {
    'dsn': 'http://8f3cfd4d83e34c899fc1ec9e7d803d73:996d9f459a944d988ae707939035e95c@sentry.xiaolumm.com/9',
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    'release': raven.fetch_git_sha(PROJECT_ROOT),
}

# STATSD_CELERY_SIGNALS = True
########################### PROMETHEUS ################################
MIDDLEWARE_CLASSES = (
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    'django_statsd.middleware.GraphiteMiddleware',
) + MIDDLEWARE_CLASSES

MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
    'django_prometheus.middleware.PrometheusAfterMiddleware',
    'dogslow.WatchdogMiddleware',
)
########################### DOGSLOW FOR PROMETHEUS ################################
# Watchdog is enabled by default, to temporarily disable, set to False:
DOGSLOW = True

# By default, Watchdog will create log files with the backtraces.
# You can also set the location of where it stores them:
DOGSLOW_LOG_TO_FILE = False

# Log requests taking longer than 25 seconds:
DOGSLOW_TIMER = 3

# Also log to this logger (defaults to none):
DOGSLOW_LOGGER = 'dogslow'
DOGSLOW_LOG_LEVEL = 'WARNING'

# Print (potentially huge!) local stack variables (off by default, use
# True for more detailed, but less manageable reports)
DOGSLOW_STACK_VARS = False

