import json
from django.http import HttpResponse
from djangorestframework.utils import as_tuple
from django.contrib.auth.decorators import login_required
from shopback.base.views import ListModelView
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

