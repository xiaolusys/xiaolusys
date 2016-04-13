# coding: utf-8
import urllib

from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe


def get_pagination_row(paginator,
                       p,
                       view,
                       kdict={},
                       page_threshold=5,
                       page_key='p',
                       anchor='', params={}):
    template_div = '<nav><ul class="pagination">%s</ul></nav>'
    template_current_page = '<li class="active"><a href="%(url)s">%(pn)s</a></li>'
    template_first_page = '<li><a href="%(url)s" aria-label="Previous">&laquo;</a></li>'
    template_next_page = '<li><a href="%(url)s" aria-label="Next">&raquo;</a></li>'
    template_with_number = '<li><a href="%(url)s">%(pn)s</a><li>'
    template_with_ellipsis = '<li><span>...</span></li>'

    def _get_kwargs(p):
        kwargs = {page_key: p}
        if kdict:
            kwargs.update(kdict)
        return kwargs

    def _get_url(view, p):
        kdict.update({page_key: p})
        if anchor:
            url = '%s%s' % (reverse(view, kwargs=_get_kwargs(p)), anchor)
        else:
            url = reverse(view, kwargs=_get_kwargs(p))
        if params:
            url = '%s?%s' % (url, urllib.urlencode(params))
        return url

    def _add_page_link(pagination_row, template, p):
        pagination_row.append(template % {'url': _get_url(view, p), 'pn': p,})

    num_pages = paginator.num_pages
    page = paginator.page(p)

    if num_pages < 1:
        return None
    pagination_row = []
    pagination_row.append('<li><span>%d/共%d页</span></li>' %
                          (page.number, num_pages))
    if page.number > 1:
        _add_page_link(pagination_row, template_first_page,
                       page.previous_page_number())
    if page.number < page_threshold:
        for pn in range(1, page.number):
            _add_page_link(pagination_row, template_with_number, pn)
        _add_page_link(pagination_row, template_current_page, page.number)
    else:
        _add_page_link(pagination_row, template_with_number, '1')
        pagination_row.append(template_with_ellipsis)
        for pn in range(page.number - 3, page.number):
            _add_page_link(pagination_row, template_with_number, pn)
        _add_page_link(pagination_row, template_current_page, page.number)

    last_pn = paginator.page_range[-1]
    if last_pn - page.number < page_threshold:
        for pn in range(page.number + 1, last_pn + 1):
            _add_page_link(pagination_row, template_with_number, pn)
    else:
        for pn in range(page.number + 1, page.number + 3):
            _add_page_link(pagination_row, template_with_number, pn)
        pagination_row.append(template_with_ellipsis)
        _add_page_link(pagination_row, template_with_number, last_pn)
    if page.number < last_pn:
        _add_page_link(pagination_row, template_next_page,
                       page.next_page_number())
    if pagination_row:
        pagination_row = mark_safe(template_div % ('\n'.join(pagination_row)))
    return pagination_row
