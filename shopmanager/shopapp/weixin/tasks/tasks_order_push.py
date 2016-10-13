# encoding=utf8
from datetime import datetime, timedelta
from celery.task import task
from shopapp.weixin.weixin_push import WeixinPush
from flashsale.pay.models.teambuy import TeamBuy, TeamBuyDetail


@task
def task_pintuan_success_push(teambuy):
    details = TeamBuyDetail.objects.filter(teambuy_id=teambuy.id)
    customers = [x.customer for x in details]

    push = WeixinPush()
    for customer in customers:
        push.push_pintuan_success(teambuy, customer)


@task
def task_pintuan_fail_push(teambuy):
    details = TeamBuyDetail.objects.filter(teambuy_id=teambuy.id)
    customers = [x.customer for x in details]

    push = WeixinPush()
    for customer in customers:
        push.push_pintuan_fail(teambuy, customer)


@task
def task_pintuan_need_more_people_push():
    expire_time = datetime.now() + timedelta(hours=6)
    teambuys = TeamBuy.objects.filter(status=0, limit_time__lte=expire_time)  # 开团状态

    for teambuy in teambuys:
        details = TeamBuyDetail.objects.filter(teambuy_id=teambuy.id)
        customers = [x.customer for x in details]

        push = WeixinPush()
        for customer in customers:
            push.push_pintuan_need_more_people(teambuy, customer)
