# coding=utf-8
import datetime
from rest_framework import status
from rest_framework import authentication
from rest_framework import filters
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import exceptions

from flashsale.protocol import serializers
from flashsale.protocol.models import APPFullPushMessge
from apis.v1.fullpush import create_app_push_msg, delete_app_push_msg_by_id, update_app_push_msg_by_id, \
    push_msg_right_now_by_id


class APPFullPushMessgeFilter(filters.FilterSet):
    class Meta:
        model = APPFullPushMessge
        fields = [
            'push_time',
            'status'
        ]


def get_apppushmsg_params_ks():
    # type: () -> Dict[List[str]]
    """返回固定key 仅仅为前端使用
    """
    from flashsale.protocol.constants import TARGET_TYPE_MODELIST, TARGET_TYPE_WEBVIEW, TARGET_TYPE_ACTIVE, \
        TARGET_TYPE_CATEGORY_PRO

    return {
        TARGET_TYPE_MODELIST: ['params_model_id'],
        TARGET_TYPE_WEBVIEW: ['params_is_native', 'params_url'],
        TARGET_TYPE_ACTIVE: ['params_activity_id'],
        TARGET_TYPE_CATEGORY_PRO: ['params_cid']
    }


def get_apppushmsg_params_kvs():
    # type: () -> Dict[str, Any]
    from flashsale.protocol.constants import TARGET_TYPE_MODELIST, TARGET_TYPE_WEBVIEW, TARGET_TYPE_ACTIVE, \
        TARGET_TYPE_CATEGORY_PRO
    from flashsale.promotion.models import ActivityEntry
    from supplychain.supplier.models import SaleCategory

    now = datetime.datetime.now()
    activity_ids = []
    for i in ActivityEntry.objects.filter(end_time__gt=now, is_active=True).values('id'):
        activity_ids.append({'name': i['id'], 'value': i['id']})
    cates = SaleCategory.objects.filter(status=SaleCategory.NORMAL, is_parent=True)
    cids = []
    for ca in cates:
        cids.append({'value': ca.cid, 'name': ca.full_name})
    return {
        TARGET_TYPE_MODELIST: [
            {'name': '款式id', 'key': 'model_id', 'value': []}
        ],
        TARGET_TYPE_WEBVIEW: [
            {'name': '显示原生导航', 'key': 'is_native',
             'value': [{'value': 0, 'name': u'不显示'}, {'value': 1, 'name': u'显示'}]},
            {'name': 'RUL', 'key': 'url', 'value': []},
        ],
        TARGET_TYPE_ACTIVE: [
            {'name': '活动id', 'key': 'activity_id', 'value': activity_ids},
        ],
        TARGET_TYPE_CATEGORY_PRO: [
            {'name': '分类产品', 'key': 'cid', 'value': cids},
        ]
    }


class APPFullPushMessgeViewSet(viewsets.ModelViewSet):
    queryset = APPFullPushMessge.objects.all().order_by('-push_time')
    serializer_class = serializers.APPPushMessgeSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser, permissions.DjangoModelPermissions)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = APPFullPushMessgeFilter

    @list_route(methods=['get'])
    def list_filters(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        return Response({
            'params_kvs': get_apppushmsg_params_kvs(),
            'status': APPFullPushMessge.STATUSES,
            'target_url': APPFullPushMessge.TARGET_CHOICES,
            'platform': APPFullPushMessge.PLATFORM_CHOICES,
        })

    def get_params_by_request(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> HttpRequest
        """仅仅更新params参数
        """
        target_url = request.data.get('target_url')
        params = {}
        if target_url in get_apppushmsg_params_ks().keys():
            params_keys = get_apppushmsg_params_ks()[target_url]
            for params_key in params_keys:
                key = '_'.join(params_key.split('_')[1:])
                if key == 'activity_id':
                    from flashsale.promotion.models import ActivityEntry
                    act_link = ActivityEntry.objects.get(id=request.data.get(params_key)).act_link
                    params.update({'url': act_link})
                params.update({key: request.data.get(params_key)})
        request.data.update({'params': params})

        # 参数清理
        total_params_keys = []
        for k, v in get_apppushmsg_params_ks().iteritems():
            total_params_keys.extend(v)
        none_flag = True
        for k in total_params_keys:
            if request.data.has_key(k):
                f = request.data.pop(k)
                if f is not None:
                    none_flag = False
        if none_flag:
            request.data.pop('params')  # 应为params全部是None 则不需要更新
        return request

    def create(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        request = self.get_params_by_request(request)
        try:
            desc = request.data.pop('desc')
            platform = request.data.pop('platform')
            push_time = datetime.datetime.strptime(request.data.pop('push_time'),
                                                   '%Y-%m-%d %H:%M:%S')
            p = create_app_push_msg(desc, platform, push_time, **request.data)
        except Exception as e:
            raise exceptions.APIException(e.message)
        serializer = self.get_serializer(p)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        try:
            delete_app_push_msg_by_id(int(kwargs.get('pk')))
        except Exception as e:
            raise exceptions.APIException(e.message)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        request = self.get_params_by_request(request)
        try:
            push_time = datetime.datetime.strptime(request.data.pop('push_time'),
                                                   '%Y-%m-%d %H:%M:%S')
            request.data.update({'push_time': push_time})
            update_app_push_msg_by_id(int(kwargs.get('pk')), **request.data)
            instance = self.get_object()
            serializer = self.get_serializer(instance)
        except Exception as e:
            raise exceptions.APIException(e.message)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def push_msg(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        """推送指定记录
        """
        flag = push_msg_right_now_by_id(int(kwargs.get('pk')))
        code = 0 if flag else 1
        info = '操作成功' if flag else '操作出错'
        return Response({'code': code, 'info': info})
