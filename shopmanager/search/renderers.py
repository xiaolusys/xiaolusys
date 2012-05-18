import json
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.template import RequestContext, loader
from djangorestframework.renderers import JSONRenderer ,TemplateRenderer
from djangorestframework.utils.mediatypes import get_media_type_params
from chartit import Chart,PivotChart

class ChartJSONRenderer(JSONRenderer):
    """
    Renderer which serializes to JSON
    """
    media_type = 'application/json'
    format = 'json'

    def render(self, obj=None, media_type=None):
        """
        Renders *obj* into serialized JSON.
        """

        if type(obj) is dict:
            obj = {"code":0,"response_content":obj}
        else:
            obj = {"code":1,"response_error":obj}

        class ChartEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (Chart,PivotChart)):
                    return obj.hcoptions #Serializer().serialize
                return DateTimeAwareJSONEncoder.default(self, obj)

        # If the media type looks like 'application/json; indent=4', then
        # pretty print the result.
        indent = get_media_type_params(media_type).get('indent', None)
        sort_keys = False
        try:
            indent = max(min(int(indent), 8), 0)
            sort_keys = True
        except (ValueError, TypeError):
            indent = None

        return json.dumps(obj, cls=ChartEncoder, indent=indent, sort_keys=sort_keys)


class ChartTemplateRenderer(TemplateRenderer):

    media_type = 'text/html'
    format = 'chart'
    template = "chart_render_template.html"

    def render(self, obj=None, media_type=None):
        """
        Renders *obj* using the :attr:`template` specified on the class.
        """
        if type(obj) is not dict:
            return obj

        template = loader.get_template(self.template)
        context = RequestContext(self.view.request, obj)
        return template.render(context)



class SearchRankHTMLRenderer(TemplateRenderer):
    """
    Renderer which provides a browsable HTML interface for an API.
    See the examples at http://api.django-rest-framework.org to see this in action.
    """

    media_type = 'text/html'
    format = 'html'
    template = 'search_rank_template.html'

    def render(self, obj=None, media_type=None):
        """
        Renders *obj* using the :attr:`template` specified on the class.
        """
        if type(obj) is not dict:
            return obj

        template = loader.get_template(self.template)
        context = RequestContext(self.view.request, obj)
        return template.render(context)



class RankChartHtmlRenderer(ChartTemplateRenderer):
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



class OrderNumPiovtChartHtmlRenderer(RankChartHtmlRenderer):
    """
    Renderer which serializes to JSON
    """
    template = ""

