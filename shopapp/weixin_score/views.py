# -*- coding:utf-8 -*-
import re
import time
import datetime
import json
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.db import models, transaction

from shopapp.weixin.models import WeiXinUser, WeixinUserScore, VipCode
from .models import SampleFrozenScore
import logging

logger = logging.getLogger("django.request")


class FrozenScoreView(View):
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        content = request.REQUEST
        commited = False
        try:
            openid = request.COOKIES.get('openid')
            sample_id = content.get('sample_id')
            frozen_score = int(content.get('frozen_score'))

            wx_user = WeiXinUser.objects.get(openid=openid)
            wx_user_score, state = WeixinUserScore.objects.get_or_create(user_openid=openid)
            sample_score, state = SampleFrozenScore.objects.get_or_create(user_openid=openid, sample_id=sample_id)

            if (frozen_score <= 0 or frozen_score % 10 != 0 or
                        wx_user_score.user_score < frozen_score or
                            sample_score.frozen_score + frozen_score > 50):
                raise Exception(u'冻结积分数量非小等于50的10倍数')

            score_vip_count = frozen_score / 10
            sample_frozen_score, state = SampleFrozenScore.objects.get_or_create(user_openid=openid,
                                                                                 sample_id=sample_id)

            transaction.commit()

            # 先减掉用户积分
            WeixinUserScore.objects.filter(user_openid=openid) \
                .update(user_score=models.F('user_score') - frozen_score)

            # 再冻结用户积分
            sample_frozen_score.frozen_score = models.F('frozen_score') + frozen_score
            sample_frozen_score.frozen_time = datetime.datetime(2014, 10, 19, 23)
            sample_frozen_score.save()

            # 增加用户VIP码使用次数
            VipCode.objects.filter(owner_openid=wx_user) \
                .update(usage_count=models.F('usage_count') + score_vip_count)
        except Exception, exc:
            logger.error(u'积分冻结失败:%s' % exc.message, exc_info=True)

            response = {"code": "bad", 'error': exc.message}
        else:
            commited = True

            response = {"code": "good",
                        "frozen_score": frozen_score}

        response = HttpResponse(json.dumps(response), content_type='application/json')
        if commited:
            transaction.commit()
        else:
            transaction.rollback()

        return response

    get = post
