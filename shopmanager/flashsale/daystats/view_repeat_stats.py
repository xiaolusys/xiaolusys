from __future__ import division
# coding=utf-8
__author__ = 'yann'
from django.views.generic import View
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db import connection
import datetime
from calendar import monthrange
from flashsale.clickrebeta.models import StatisticsShopping


def get_new_user(user_data, old_user):
    new_user = []
    for val in user_data:
        if val not in old_user:
            new_user.append(val[0])
    return new_user


class StatsRepeatView(View):
    @staticmethod
    def get(request):
        content = request.REQUEST
        today = datetime.date.today()
        start_time_str = content.get("df", None)
        end_time_str = content.get("dt", None)
        if start_time_str:
            year, month, day = start_time_str.split('-')
            start_date = datetime.date(int(year), int(month), int(day))
            if start_date > today:
                start_date = today
        else:
            start_date = today - datetime.timedelta(days=monthrange(today.year, today.month)[1])
        if end_time_str:
            year, month, day = end_time_str.split('-')
            end_date = datetime.date(int(year), int(month), int(day))
        else:
            end_date = today
        """找出选择的开始月份和结束月份"""
        start_month = start_date.month
        end_month = end_date.month
        month_march = "2015-03-01"
        stats_month_range = range(start_month, end_month)
        month_range = range(start_month + 1, end_month + 1)
        result_data_list = []
        all_result_data_list = []
        try:
            for target_month in stats_month_range:
                month_date_begin = datetime.datetime(start_date.year, target_month, 1)
                month_date_end = datetime.datetime(start_date.year, target_month + 1, 1)

                """找出目标月的所有购买用户"""
                user_sql = 'select openid from flashsale_tongji_shopping where shoptime>="{0}" and shoptime<="{1}" and openid!="" group by openid'.format(
                    month_date_begin, month_date_end)
                cursor = connection.cursor()
                cursor.execute(user_sql)
                user_data = cursor.fetchall()
                all_user_num = len(user_data)

                """找出目标月之前的所有用户"""
                old_user_sql = 'select openid from flashsale_tongji_shopping where shoptime<="{0}" and shoptime>="{1}" group by openid'.format(
                    month_date_begin, month_march)
                cursor.execute(old_user_sql)
                old_user_data = cursor.fetchall()

                new_user = get_new_user(user_data, old_user_data)
                new_user_quantity = len(new_user)
                result_data_dict = {"month": target_month, "new_user": new_user_quantity}
                user_data_list = []
                for i in month_range:
                    if target_month >= i:
                        user_data_list.append("None")
                    else:
                        stats_date_begin = datetime.datetime(start_date.year, i, 1)
                        stats_date_end = datetime.datetime(start_date.year, i + 1, 1)
                        count_month = StatisticsShopping.objects.filter(
                            shoptime__range=(stats_date_begin, stats_date_end)).filter(openid__in=new_user).values(
                            'openid').distinct().count()

                        temp_dict = {"num": count_month, "rec_num": float(
                            '%0.2f' % (count_month * 100 / new_user_quantity if new_user_quantity else 0))}
                        user_data_list.append(temp_dict)
                result_data_dict["user_data"] = user_data_list
                result_data_list.append(result_data_dict)

                all_user_data_list = []
                all_result_data_dict = {"month": target_month, "all_user_num": all_user_num}
                print user_data
                for i in month_range:
                    if target_month >= i:
                        all_user_data_list.append("None")
                    else:
                        all_user_data = [val[0] for val in user_data]
                        stats_date_begin = datetime.datetime(start_date.year, i, 1)
                        stats_date_end = datetime.datetime(start_date.year, i + 1, 1)
                        count_month = StatisticsShopping.objects.filter(
                            shoptime__range=(stats_date_begin, stats_date_end)).filter(openid__in=all_user_data).values(
                            'openid').distinct().count()
                        temp_dict = {"num": count_month, "rec_num": float(
                            '%0.2f' % (count_month * 100 / all_user_num if all_user_num else 0))}
                        all_user_data_list.append(temp_dict)
                all_result_data_dict["user_data"] = all_user_data_list
                all_result_data_list.append(all_result_data_dict)
        finally:
            cursor.close()
        return render_to_response("xiaolumm/data2repeatshop.html",
                                  {"all_data": result_data_list, "all_result_data_list": all_result_data_list,
                                   "start_date": start_date, "end_date": end_date, "month_range": month_range},
                                  context_instance=RequestContext(request))