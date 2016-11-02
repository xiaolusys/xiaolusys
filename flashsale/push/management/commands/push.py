# coding: utf-8

import json
from optparse import make_option
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from flashsale.protocol import get_target_url
from flashsale.protocol import constants as protocol_constants
from flashsale.push.mipush import mipush_of_ios, mipush_of_android

PUSH_BY_REGID = 'regid'
PUSH_BY_ACCOUNT = 'account'
PUSH_BY_TOPIC = 'topic'
PUSH_ALL = 'all'


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (make_option(
        '-t',
        '--title',
        dest='title',
        action='store',
        help='推送标题'), make_option('-p',
                                  '--platform',
                                  dest='platform',
                                  action='store',
                                  help='推送平台'), make_option('-q',
                                                            '--query',
                                                            dest='params',
                                                            action='append',
                                                            help='跳转参数'))

    def handle(self, *args, **kwargs):
        platform = kwargs.get('platform') or 'ios'
        mipush = mipush_of_ios if platform == 'ios' else mipush_of_android
        push_type, target_type = args[:2]
        target_type = int(target_type)

        params = []
        for p in kwargs.get('params') or []:
            params.append(p.split('='))
        params = dict(params)
        target_url = get_target_url(target_type, params)
        print target_url

        if push_type == PUSH_BY_REGID:
            regid, desc = args[2:4]
            mipush.push_to_regid(regid.strip(),
                                 {'target_url': target_url},
                                 description=desc)
        elif push_type == PUSH_BY_ACCOUNT:
            customer_id, desc = args[2:4]
            customer_id = int(customer_id)
            mipush.push_to_account(customer_id,
                                   {'target_url': target_url},
                                   description=desc)
        elif push_type == PUSH_BY_TOPIC:
            topic, desc = args[2:4]
            mipush.push_to_topic(topic,
                                 {'target_url': target_url},
                                 description=desc)
        elif push_type == PUSH_ALL:
            desc = args[2]
            mipush.push_to_all({'target_url': target_url}, description=desc)
