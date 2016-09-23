# coding: utf-8
from __future__ import unicode_literals
from django.core.paginator import InvalidPage, Paginator as DjangoPaginator
from django.utils import six

from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination

class PageNumberPkPagination(PageNumberPagination):
    def paginate_pks(self, queryset, request, view=None, pk_alias='id'):
        """
        Paginate a queryset if required, either returning a
        page object, or `None` if pagination is not configured for this view.
        """
        self._handle_backwards_compat(view)

        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = DjangoPaginator(queryset, page_size)
        page_number = request.query_params.get(self.page_query_param, 1)
        if page_number in self.last_page_strings:
            page_number = paginator.num_pages

        try:
            self.page = paginator.page(page_number)
        except InvalidPage as exc:
            msg = self.invalid_page_message.format(
                page_number=page_number, message=six.text_type(exc)
            )
            raise NotFound(msg)

        if paginator.count > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True

        self.request = request
        return self.page.object_list.values_list(pk_alias, flat=True)