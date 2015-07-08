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
from django.db.models import Sum
from flashsale.xiaolumm.models import XiaoluMama
from django.conf import settings
from shopapp.weixin.models import get_Unionid
from flashsale.daystats.tasks import task_calc_xlmm


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
        finally:
            cursor.close()
        return render_to_response("xiaolumm/data2repeatshop.html",
                                  {"all_data": result_data_list, "start_date": start_date, "end_date": end_date,
                                   "month_range": month_range},
                                  context_instance=RequestContext(request))


from flashsale.daystats.models import DailyStat
from shopback.trades.models import MergeTrade


class StatsSaleView(View):
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

        month_range = range(start_month, end_month + 1)
        result_list = []
        for month in month_range:
            month_start_date = datetime.date(start_date.year, month, 1)
            month_end_date = datetime.date(end_date.year, month + 1, 1)
            total_sale_amount = DailyStat.objects.filter(day_date__gte=month_start_date,
                                                         day_date__lt=month_end_date).aggregate(
                total_sale_amount=Sum('total_payment')).get('total_sale_amount') or 0
            total_order_num = DailyStat.objects.filter(day_date__gte=month_start_date,
                                                       day_date__lt=month_end_date).aggregate(
                total_sale_order=Sum('total_order_num')).get('total_sale_order') or 0
            shoping_stats = StatisticsShopping.objects.filter(shoptime__gte=month_start_date,
                                                              shoptime__lt=month_end_date)
            total_sale_num = 0
            sm = {}
            for shop_stat in shoping_stats:
                tm = '%s-%s-%s' % (shop_stat.shoptime.year, shop_stat.shoptime.month, shop_stat.shoptime.day)
                if tm in sm:
                    sm[tm].add(shop_stat.openid)
                else:
                    sm[tm] = set([shop_stat.openid])
            for s, m in sm.iteritems():
                total_sale_num += len(m)

            total_package_num = MergeTrade.objects.filter(type__in=("sale", "wx")).exclude(weight_time=None).filter(
                sys_status=u'FINISHED').filter(pay_time__gte=month_start_date, pay_time__lt=month_end_date).count()
            result_list.append(
                {"month": month, "total_sale_amount": total_sale_amount / 100, "total_order_num": total_order_num,
                 "total_package_num": total_package_num, "total_sale_num": total_sale_num})
        return render_to_response("xiaolumm/data2sale.html",
                                  {"month_range": month_range, "result_list": result_list, "start_date": start_date,
                                   "end_date": end_date},
                                  context_instance=RequestContext(request))


class StatsSalePeopleView(View):
    @staticmethod
    def get(request):
        content = request.REQUEST
        start_time_str = content.get("df", None)
        end_time_str = content.get("dt", None)
        print start_time_str,end_time_str
        send_tasks = task_calc_xlmm.delay(start_time_str, end_time_str)
        print send_tasks
        return render_to_response("xiaolumm/data2salepeople.html",
                                  {"task_id": send_tasks},
                                  context_instance=RequestContext(request))