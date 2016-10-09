# -*-coding:utf-8 -*-

APP_KEY = '12545735'
SESSION = '6100013704d43273f44071e4a2ae123429ba28420068f5e174265168'

param_waybill_cloud_print_apply_new_request = {'cp_code': "STO",
                                               'sender': {'name': '李家帅',
                                                          'mobile': '15026869609',
                                                          'address': {
                                                              "city": "上海市",
                                                              "detail": "佘山镇吉业路245号",
                                                              "district": "松江区",
                                                              "province": "上海"
                                                          }
                                                          },
                                               'trade_order_info_dtos': {
                                                   "object_id": '123',
                                                   "order_info": {
                                                       "order_channels_type": "TB",
                                                       "trade_order_list": "132112"
                                                   },
                                                   "package_info": {
                                                       "items": {
                                                           "count": 1,
                                                           "name": "衣服"
                                                       }
                                                   },
                                                   "recipient": {
                                                       "address": {
                                                           "detail": "wojia",
                                                           "province": "shanghai"
                                                       },
                                                       "name": "denghui",
                                                       "mobile": "15800972458"
                                                   },
                                                   "template_url": "http://cloudprint.cainiao.com/cloudprint/template/getStandardTemplate.json?template_id=1001",
                                                   'user_id': '12545735'
                                               }
                                               }
