# coding=utf-8
import datetime

import os
from django.conf import settings
from common.utils import CSVUnicodeWriter
from celery.task import task

REPORT_DIR = 'report'


@task()
def task_make_Manager_Summary_Cvs(file_dir=None):
    print 'summary task is running .....'
    from .views import manage_Summar
    yestoday = datetime.datetime.today() - datetime.timedelta(days=1)
    date_time = datetime.datetime(yestoday.year, yestoday.month, yestoday.day, 23, 59, 59)
    data = manage_Summar(date_time)  # 字典列表[{"a":1},{"b":2}]
    if not file_dir:
        file_dir = os.path.join(settings.DOWNLOAD_ROOT, REPORT_DIR)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
    field_name_list = [(u'管理员', 'username'), (u'订单数量', 'sum_ordernumcount'), (u'购买人数', 'sum_buyercount'),
                       (u'UV', 'uv_summary'), (u'PV', 'pv_summary'),
                       (u'转化率', 'conversion_rate'), (u'代理人数', 'xlmm_num'),
                       (u'活跃度', 'activity'), (u'有效点击', 'sum_click_valid')]
    file_name = u'manager_summary_{0}_{1}_{2}.csv'.format(date_time.year, date_time.month, date_time.day)
    file_path_name = os.path.join(file_dir, file_name)

    print file_path_name
    with open(file_path_name, 'w+') as myfile:
        writer = CSVUnicodeWriter(myfile, encoding='gbk')
        thead = [k[0] for k in field_name_list]
        writer.writerow(thead)
        for i in data:
            ivalues = [str(i[k[1]]) for k in field_name_list]
            writer.writerow(ivalues)
