# coding=utf-8
from rest_framework import authentication, renderers, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import CategorySaleStat
import datetime
from django.db.models import Sum
from .models import ProductCategory
from operator import itemgetter


class CategoryStatViewSet(APIView):
    authentication_classes = (authentication.SessionAuthentication, authentication.BaseAuthentication)
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = CategorySaleStat.objects.all()
    template_name = "categorysalestat/category_stat.html"

    def get(self, request):
        """ 总结过滤时间段的分类统计数据 """
        content = request.REQUEST
        today = datetime.datetime.today()
        df = content.get("df", None)
        dt = content.get("dt", None)
        category = content.get("choose_category", 0)  # 0 表示全部，　1　表示童装，　2　表示女装
        title = "产品分类统计"
        # 分类童装和女装
        df = datetime.datetime.strptime(df, '%Y-%m-%d') if df is not None else today - datetime.timedelta(days=7)
        dt = datetime.datetime.strptime(dt, '%Y-%m-%d') if dt is not None else today
        queryset = self.queryset.filter(stat_date__gte=df, stat_date__lte=dt)
        if int(category) == 1:  # 过滤童装
            category = ProductCategory.objects.filter(parent_cid=5).values('cid')
            queryset = queryset.filter(category__in=category)
        elif int(category) == 2:  # 过滤女装
            category = ProductCategory.objects.filter(parent_cid=8).values('cid')
            queryset = queryset.filter(category__in=category)
        calcu_value, key_svlues = self.calculate_by_queryset(queryset)
        return Response(
            {"title": title, "df": df.date(), "dt": dt.date(), "calcu_value": calcu_value, "key_svlues": key_svlues})

    def calculate_by_queryset(self, queryset):
        """ 计算 """
        sum_values = queryset.values("category").annotate(
            s_sale_amount=Sum("sale_amount"), s_sale_num=Sum("sale_num"),
            s_pit_num=Sum("pit_num"), s_collect_num=Sum("collect_num"),
            s_collect_amount=Sum("collect_amount"), s_stock_num=Sum("stock_num"),
            s_stock_amount=Sum("stock_amount"), s_refund_num=Sum("refund_num"),
            s_refund_amount=Sum("refund_amount"))
        # 获取类别名称
        data = []
        key_svlues = {k: sum(map(itemgetter(k), sum_values)) for k in sum_values[0]}
        percent = lambda x, y: round(x * 100.0 / y, 3) if y > 0 else 0
        division = lambda x, y: round(x * 1.0 / y) if y > 0 else 0
        for i in sum_values:
            category = int(i['category'])
            try:
                category = ProductCategory.objects.get(cid=category)
                category_full_name = category.__unicode__()
            except ProductCategory.DoesNotExist:
                category_full_name = "NoCategory"
            category_name = "%s" % category_full_name
            i['category'] = category_name
            # 除以总值的占比
            i['s_stock_amount_p'] = percent(i['s_stock_amount'], key_svlues['s_stock_amount'])
            i['s_collect_num_p'] = percent(i['s_collect_num'], key_svlues['s_collect_num'])
            i['s_sale_num_p'] = percent(i['s_sale_num'], key_svlues['s_sale_num'])
            i['s_pit_num_p'] = percent(i['s_pit_num'], key_svlues['s_pit_num'])
            i['s_stock_num_p'] = percent(i['s_stock_num'], key_svlues['s_stock_num'])
            i['s_sale_amount_p'] = percent(i['s_sale_amount'], key_svlues['s_sale_amount'])
            i['s_refund_num_p'] = percent(i['s_refund_num'], key_svlues['s_refund_num'])
            i['s_refund_amount_p'] = percent(i['s_refund_amount'], key_svlues['s_refund_amount'])
            i['s_collect_amount_p'] = percent(i['s_collect_amount'], key_svlues['s_collect_amount'])

            i['sigle_output'] = division(i['s_sale_amount'], i['s_pit_num'])  # 单坑产出　销售额　除以　坑位数量
            i['sigle_sale'] = division(i['s_sale_num'], i['s_pit_num'])  # 单坑销量 销售数量　除以　坑位数量
            i['average_price'] = division(i['s_sale_amount'], i['s_sale_num'])  # 平均价格　销售额　除以　销售数量
            data.append(i)
        return data, key_svlues
