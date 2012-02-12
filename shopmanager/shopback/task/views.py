import json
from django.http import HttpResponse
from djangorestframework.utils import as_tuple
from djangorestframework import status,signals
from djangorestframework.response import Response
from djangorestframework.mixins import CreateModelMixin
from djangorestframework.views import ModelView
from django.contrib.auth.decorators import login_required
from shopback.base.views import ListModelView
from shopback.task.models import UNEXECUTE
from auth import apis

class ListItemTaskView(ListModelView):
    queryset = None

    def get(self, request, *args, **kwargs):
        model = self.resource.model
        visitor_id = request.session['top_parameters']['visitor_id']

        queryset = self.get_queryset() if self.get_queryset() is not None else model.objects.all()

        if hasattr(self, 'resource'):
            ordering = getattr(self.resource, 'ordering', None)
        else:
            ordering = None

        kwargs.update({'user_id':visitor_id})

        if ordering:
            args = as_tuple(ordering)
            queryset = queryset.order_by(*args)
        return queryset.filter(**kwargs)

    def get_queryset(self):
        return self.queryset


class CreateListItemTaskModelView(CreateModelMixin,ModelView):
    """A view which provides default operations for create, against a model in the database."""

    def post(self, request, *args, **kwargs):
        model = self.resource.model

        content = dict(self.CONTENT)

        all_kw_args = dict(content.items() + kwargs.items())

        update_nums = model.objects.filter(num_iid=all_kw_args['num_iid']).update(**all_kw_args)

        if update_nums == 0:

            if args:
                instance = model(pk=args[-1], **all_kw_args)
            else:
                instance = model(**all_kw_args)
            instance.save()

            signals.obj_created.send(sender=model, obj=instance, request=self.request)

        else:
            instance = model.objects.get(num_iid=all_kw_args['num_iid'],status=UNEXECUTE)

        headers = {}
        if hasattr(instance, 'get_absolute_url'):
            headers['Location'] = self.resource(self).url(instance)
        return Response(status.HTTP_201_CREATED, instance, headers)


@login_required
def direct_update_listing(request,num_iid,num):

    if not (num_iid.isdigit() and num.isdigit()):
        response = {'errormsg':'The num_iid and num must be number!'}
        return HttpResponse(json.dumps(response),mimetype='application/json')

    response = apis.taobao_item_update_listing(num_iid,num,request.session.get('top_session'))

    return HttpResponse(json.dumps(response),mimetype='application/json')


@login_required
def direct_del_listing(request,num_iid):

    if not num_iid.isdigit():
        response = {'errormsg':'The num_iid  must be number!'}
        return HttpResponse(json.dumps(response),mimetype='application/json')

    response = apis.taobao_item_update_delisting(num_iid,request.session.get('top_session'))

    return HttpResponse(json.dumps(response),mimetype='application/json')

