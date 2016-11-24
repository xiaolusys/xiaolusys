# encoding=utf8
from shopmanager import celery_app as app
from mall.xiaolupay.apis.v1.envelope import WeixinRedEnvelopAPI
from mall.xiaolupay.models.weixin_red_envelope import WeixinRedEnvelope
from flashsale.pay.models.envelope import Envelop


@app.task()
def task_sent_weixin_red_envelope(envelope_id):
    envelope = WeixinRedEnvelope.objects.filter(id=envelope_id).first()
    if not envelope or envelope.status != WeixinRedEnvelope.UNSEND:
        return

    api = WeixinRedEnvelopAPI()
    api.createEnvelop(envelope)


@app.task()
def task_sync_weixin_red_envelope(envelope_id):
    """
    定时同步微信红包信息
    """
    envelope = WeixinRedEnvelope.objects.filter(id=envelope_id).first()
    if not envelope or envelope.status == WeixinRedEnvelope.UNSEND:
        return

    api = WeixinRedEnvelopAPI()
    envelope = api.queryEnvelope(envelope)

    item = Envelop.objects.filter(envelop_id=envelope.mch_billno).first()
    item.handle_envelop(envelope)
