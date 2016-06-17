# coding=utf-8
import datetime
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from statistics import serializers
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import APIException
from statistics.models import SaleStats
from statistics import constants


class SaleStatsViewSet(viewsets.ModelViewSet):
    queryset = SaleStats.objects.all()
    serializer_class = serializers.StatsSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def list(self, request, *args, **kwargs):
        queryset = self.queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def get_type_list(self, request):
        """ 获取总计 不分页 """
        content = request.REQUEST
        timely_type = content.get('timely_type') or None
        record_type = content.get('record_type') or None
        date_field = content.get('date_field') or None
        current_id = content.get('current_id') or None
        status = content.get('status') or None
        date_field_from = content.get('date_field_from') or None
        date_field_to = content.get('date_field_to') or None
        queryset = self.queryset
        if timely_type:
            queryset = queryset.filter(timely_type=timely_type)
        if record_type:
            queryset = queryset.filter(record_type=record_type)
        if status:
            queryset = queryset.filter(status=status)
        if date_field:
            queryset = queryset.filter(date_field=date_field)
        if current_id:
            queryset = queryset.filter(current_id=current_id)
        if date_field_from and date_field_to:
            queryset = queryset.filter(date_field__gte=date_field_from, date_field__lte=date_field_to)
        queryset = queryset.order_by('num')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def get_all_num_type_list(self, request):
        """ 获取总计 不分页 使用了计算　其他状态数量的　serializer """
        content = request.REQUEST
        timely_type = content.get('timely_type') or None
        record_type = content.get('record_type') or None
        date_field = content.get('date_field') or None
        current_id = content.get('current_id') or None
        status = content.get('status') or None
        limit = int(content.get('limit') or 0)
        date_field_from = content.get('date_field_from') or None
        date_field_to = content.get('date_field_to') or None
        queryset = self.queryset
        if date_field_from and date_field_to:
            queryset = queryset.filter(date_field__gte=date_field_from,
                                       date_field__lte=date_field_to)
        if timely_type:
            queryset = queryset.filter(timely_type=timely_type)
        if record_type:
            queryset = queryset.filter(record_type=record_type)
        if status:
            queryset = queryset.filter(status=status)
        if date_field:
            queryset = queryset.filter(date_field=date_field)
        if current_id:
            queryset = queryset.filter(current_id=current_id)
        if limit:
            queryset = queryset.order_by('-num')[:limit]
        serializer = serializers.StatsAllNumSerializer(queryset,
                                                       many=True,
                                                       context={'request': request})
        return Response(serializer.data)

    @list_route(methods=['get'])
    def get_annotate_type_list(self, request):
        """ 获取总计 不分页 使用了计算　其他状态数量的　serializer """
        content = request.REQUEST
        timely_type = content.get('timely_type') or None
        record_type = content.get('record_type') or None
        status = content.get('status') or None
        limit = int(content.get('limit') or 0)
        date_field_from = content.get('date_field_from') or None
        date_field_to = content.get('date_field_to') or None
        queryset = self.queryset
        if date_field_from and date_field_to:
            queryset = queryset.filter(date_field__gte=date_field_from,
                                       date_field__lte=date_field_to)
        if timely_type:
            queryset = queryset.filter(timely_type=timely_type)
        if record_type:
            queryset = queryset.filter(record_type=record_type)
        if status:
            queryset = queryset.filter(status=status)
        if limit:
            queryset = queryset.values('current_id',
                                       'name',
                                       'pic_path').annotate(s_num=Sum('num'),
                                                            s_payment=Sum('payment')).order_by(
                '-s_num')[:limit]
        data = []
        for stat in queryset:
            data.append(stat)
        return Response(data)

    @list_route(methods=['get'])
    def get_target_stats_info(self, request):
        """ 计算某一个时间段的某个current_id 的退款信息（退款数量　退货数量　实际销量　逃单数量　缺货数量）"""
        content = request.REQUEST
        record_type = content.get('record_type') or None
        current_id = content.get('current_id') or None
        date_field_from = content.get('date_field_from') or None
        date_field_to = content.get('date_field_to') or None

        if not (record_type and current_id):
            return Response({})
        queryset = self.queryset
        if date_field_from and date_field_to:
            queryset = queryset.filter(date_field__gte=date_field_from,
                                       date_field__lt=date_field_to)
        queryset = queryset.filter(current_id=current_id,
                                   record_type=record_type,
                                   timely_type=constants.TIMELY_TYPE_DATE)
        obsolete_supplier = False
        if current_id and record_type == str(constants.TYPE_SUPPLIER):
            stat = queryset.first()
            if stat:
                obsolete_supplier = stat.is_obsolete_supplier

        current_info = {"current_id": current_id, "record_type": record_type}
        s_num_payments = queryset.values('status').annotate(t_num=Sum('num'), t_payment=Sum('payment'))

        status_map = {
            0: 'nopay',
            1: "paid",
            2: "cacl",
            3: "ostk",
            4: "rtg"
        }

        default_stats_info = {
            "nopay_num": 0,
            "paid_num": 0,
            "cacl_num": 0,
            "ostk_num": 0,
            "rtg_num": 0,
            "nopay_payment": 0.0,
            "paid_payment": 0.0,
            "cacl_payment": 0.0,
            "ostk_payment": 0.0,
            "rtg_payment": 0.0,
            "obsolete_supplier": obsolete_supplier
        }
        for i in s_num_payments:
            default_stats_info[status_map[i['status']] + '_num'] = i["t_num"]
            default_stats_info[status_map[i['status']] + '_payment'] = i["t_payment"]
        default_stats_info.update(current_info)
        return Response(default_stats_info)

    @list_route(methods=['get'])
    def get_pag_type_list(self, request):
        content = request.REQUEST
        timely_type = content.get('timely_type') or None
        record_type = content.get('record_type') or None
        status = content.get('status') or None
        queryset = self.queryset
        if timely_type:
            queryset = queryset.filter(timely_type=timely_type)
        if record_type:
            queryset = queryset.filter(record_type=record_type)
        if status:
            queryset = queryset.filter(status=status)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
