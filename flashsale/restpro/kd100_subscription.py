# coding=utf-8
import requests
import logging
logger = logging.getLogger(__name__)


def kd100_subscription(company, number,query_url = "http://poll.kuaidi100.com/poll",
                        key='ZIBQxfAP7615',callbackurl="http://admin.xiaolumm.com/rest/v1/wuliu/push_wuliu_data"):
    company = str(company)
    number = str(number)

    param = '''{"company":"%s","number":"%s","key":"%s","from":"","to":"","parameters":
        {"callbackurl":"%s","salt":"","resultv2":"0","autoCom":"0","interCom":"0","departureCountry":"",
         "departureCom":"","destinationCountry":"","destinationCom":""}}''' %(company,number,key,callbackurl)
    data = {"param":param}
    resp = requests.post(query_url,data=data)
    logger.warn({'action': "kd100", 'info': "kd100_subscription:" + str(number)})
    return resp.text