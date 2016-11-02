import json
from django.template import RequestContext, loader

# from djangorestframework.utils.mediatypes import get_media_type_params
from chartit import Chart, PivotChart
from shopback.base.new_renders import new_ChartTemplateRenderer
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, RequestContext, loader, Template


class SearchRankHTMLRenderer(TemplateHTMLRenderer):
    media_type = 'text/html'
    format = 'chart'
    template_name = 'search_rank_template.html'
    exception_template_names = [
        '%(status_code)s.html',
        'api_exception.html'
    ]
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders data to HTML, using Django's standard template rendering.

        The template name is determined by (in order of preference):

        1. An explicit .template_name set on the response.
        2. An explicit .template_name set on this class.
        3. The return result of calling view.get_template_names().
        """
        if type(data) is not dict:
            return data

        renderer_context = renderer_context or {}
        view = renderer_context['view']
        request = renderer_context['request']
        response = renderer_context['response']

        if response.exception:
            template = self.get_exception_template(response)
        else:
            template_names = self.get_template_names(response, view)
            template = self.resolve_template(template_names)

        context = self.resolve_context(data, request, response)
        return template.render(context)

    def resolve_template(self, template_names):
        return loader.select_template(template_names)

    def resolve_context(self, data, request, response):
        if response.exception:
            data['status_code'] = response.status_code
        return RequestContext(request, data)

    def get_template_names(self, response, view):
        if response.template_name:
            return [response.template_name]
        elif self.template_name:
            return [self.template_name]
        elif hasattr(view, 'get_template_names'):
            return view.get_template_names()
        elif hasattr(view, 'template_name'):
            return [view.template_name]
        raise ImproperlyConfigured(
            'Returned a template response with no `template_name` attribute set on either the view or response'
        )

    def get_exception_template(self, response):
        template_names = [name % {'status_code': response.status_code}
                          for name in self.exception_template_names]

        try:
            # Try to find an appropriate error template
            return self.resolve_template(template_names)
        except Exception:
            # Fall back to using eg '404 Not Found'
            return Template('%d %s' % (response.status_code,
                                       response.status_text.title()))


class RankChartHtmlRenderer(new_ChartTemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    media_type = 'text/html'
    format = 'html'
    template = ""


class KeysChartHtmlRenderer(RankChartHtmlRenderer):
    """
    Renderer which serializes to JSON
    """
    template = "keywords_itemsrank.html"


class RankPivotChartHtmlRenderer(RankChartHtmlRenderer):
    """
    Renderer which serializes to JSON
    """
    template = "keywords_rankstatistic.html"


class AvgRankPivotChartHtmlRenderer(RankChartHtmlRenderer):
    """
    Renderer which serializes to JSON
    """
    template = "keywords_itemsrank.html"


class TradePivotChartHtmlRenderer(RankChartHtmlRenderer):
    """
    Renderer which serializes to JSON
    """
    template = ""


class TradeTopChartHtmlRenderer(RankChartHtmlRenderer):
    """
    Renderer which serializes to JSON
    """
    template = ""
