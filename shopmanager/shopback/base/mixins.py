from django.core.paginator import Paginator
from django.db.models.query import QuerySet
from django.db.models import signals
# from djangorestframework.response import ErrorResponse
# from djangorestframework import status
from rest_framework import status
from django.http import HttpResponse, Http404


class PaginatorMixin(object):
    """
    Adds pagination support to GET requests
    Obviously should only be used on lists :)
    
    A default limit can be set by setting `limit` on the object. This will also
    be used as the maximum if the client sets the `limit` GET param
    """
    limit = 100

    def get_limit(self):
        """ Helper method to determine what the `limit` should be """
        try:
            limit = int(self.request.GET.get('limit', self.limit))
            return min(limit, self.limit)
        except ValueError:
            return self.limit

    def url_with_page_number(self, page_number):
        """ Constructs a url used for getting the next/previous urls """
        url = "%s?page=%d" % (self.request.path, page_number)

        limit = self.get_limit()
        if limit != self.limit:
            url = "%s&limit=%d" % (url, limit)

        return url

    def next(self, page):
        """ Returns a url to the next page of results (if any) """
        if not page.has_next():
            return None

        return self.url_with_page_number(page.next_page_number())

    def previous(self, page):
        """ Returns a url to the previous page of results (if any) """
        if not page.has_previous():
            return None

        return self.url_with_page_number(page.previous_page_number())

    def serialize_page_info(self, page):
        """ This is some useful information that is added to the response """
        return {
            'next': self.next(page),
            'page': page.number,
            'pages': page.paginator.num_pages,
            'per_page': self.get_limit(),
            'previous': self.previous(page),
            'total': page.paginator.count,
        }

    def custom_result(self, obj):
        """we can override this to custom reponse result"""
        return obj

    def filter_response(self, obj):
        """
        Given the response content, paginate and then serialize.
        
        The response is modified to include to useful data relating to the number
        of objects, number of pages, next/previous urls etc. etc.
        
        The serialised objects are put into `results` on this new, modified
        response
        """

        # We don't want to paginate responses for anything other than GET requests
        if self.method.upper() != 'GET':
            return self._resource.filter_response(obj)

        obj = self.custom_result(obj)

        if not isinstance(obj, QuerySet):
            return self._resource.filter_response(obj)

        paginator = Paginator(obj, self.get_limit())

        try:
            page_num = int(self.request.GET.get('page', '1'))
        except ValueError:
            page_num = 1

        if page_num not in paginator.page_range:
            raise Http404({
                              'detail': 'That page contains no results'})  # ErrorResponse(status.HTTP_404_NOT_FOUND, {'detail': 'That page contains no results'})

        page = paginator.page(page_num)

        serialized_object_list = self._resource.filter_response(page.object_list)
        serialized_page_info = self.serialize_page_info(page)

        serialized_page_info['results'] = serialized_object_list

        return serialized_page_info


class CounterMixin(object):
    """docstring for CountMixin"""
    queryset = None

    def get(self, request, *args, **kwargs):
        model = self.resource.model

        queryset = self.queryset if self.queryset else model.objects.all()

        if hasattr(self, 'resource'):
            ordering = getattr(self.resource, 'ordering', None)
        else:
            ordering = None

        if ordering:
            args = as_tuple(ordering)
            queryset = queryset.order_by(*args)
        return queryset.filter(**kwargs).count()


class BatchGetMixin(object):
    """docstring for ClassName"""
    pk_field = 'pk'

    def get_queryset(self):
        """docstring for get_queryset"""
        queryset = self.queryset if self.queryset else self.resource.model.objects
        queryset = queryset.filter(status=True)

        ids = self.request.GET.get('ids', None)
        if ids:
            return queryset.filter(**{'%s__in' % self.pk_field: ids.split(',')})

        return queryset


class DeleteModelMixin(object):
    """docstring for ClassName"""

    def delete(self, request, *args, **kwargs):
        model = self.resource.model

        try:
            if args:
                # If we have any none kwargs then assume the last represents the primrary key
                instance = model.objects.get(pk=args[-1], **kwargs)
            else:
                # Otherwise assume the kwargs uniquely identify the model
                instance = model.objects.get(**kwargs)
        except model.DoesNotExist:
            raise Http404  # ErrorResponse(status.HTTP_404_NOT_FOUND, None, {})

        instance.status = False
        instance.save()

        signals.post_delete.send(sender=model, obj=instance, request=self.request)

        return


def as_tuple(obj):
    """
    Given an object which may be a list/tuple, another object, or None,
    return that object in list form.

    IE:
    If the object is already a list/tuple just return it.
    If the object is not None, return it in a list with a single element.
    If the object is None return an empty list.
    """
    if obj is None:
        return ()
    elif isinstance(obj, list):
        return tuple(obj)
    elif isinstance(obj, tuple):
        return obj
    return (obj,)
