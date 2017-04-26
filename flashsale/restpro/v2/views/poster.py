# encoding=utf8
import simplejson
from rest_framework import viewsets, renderers
from rest_framework import authentication, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.parsers import JSONParser
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response

from common.auth import WeAppAuthentication
from flashsale.pay.models import GoodShelf
from flashsale.restpro.v2.serializers.serializers import PosterSerializer


class PosterViewSet(viewsets.ModelViewSet):
    """
    """
    authentication_classes = (authentication.SessionAuthentication, WeAppAuthentication, authentication.BasicAuthentication)
    serializer_class = PosterSerializer
    queryset = GoodShelf.objects.all().order_by('-created')
    permission_classes = (permissions.IsAuthenticated, DjangoModelPermissions)
    # parser_classes = (JSONParser,)

    def create(self, req, *args, **kwargs):
        """
        POST /rest/v2/poster
        """
        data = req.data.keys()[0]
        data = simplejson.loads(data)
        title = data.get('title')
        category = data.get('category')
        items = data.get('items')
        is_active = data.get('is_active')
        active_time = data.get('active_time')

        poster = GoodShelf()
        if title:
            poster.title = title
        if category:
            poster.category = category
        if is_active is not None:
            poster.is_active = is_active
        if active_time:
            poster.active_time = active_time
        if items:
            poster.wem_posters = items
        poster.save()

        serializers = self.get_serializer(poster)
        return Response(serializers.data)

    def update(self, req, *args, **kwargs):
        """
        PUT /rest/v2/poster/<id>
        """
        pk = kwargs.get('pk')
        data = req.data
        poster = GoodShelf.objects.filter(id=pk).first()

        if not poster:
            return Response({'code': 1, 'msg': u'不存在'})

        title = data.get('title')
        category = data.get('category')
        items = data.get('items')
        is_active = data.get('is_active')
        active_time = data.get('active_time')

        if title:
            poster.title = title
        if category:
            poster.category = category
        if is_active is not None:
            poster.is_active = is_active
        if active_time:
            poster.active_time = active_time
        if items:
            poster.wem_posters = items
        poster.save()

        serializers = self.get_serializer(poster)
        return Response(serializers.data)

