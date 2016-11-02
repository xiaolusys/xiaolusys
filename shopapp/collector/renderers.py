import json
from django.template import RequestContext, loader
# from djangorestframework.renderers import JSONRenderer ,TemplateRenderer
# from djangorestframework.utils.mediatypes import get_media_type_params
from chartit import Chart, PivotChart
# from core.options.renderers import ChartTemplateRenderer




# class SearchRankHTMLRenderer(TemplateRenderer):
#     """
#     Renderer which provides a browsable HTML interface for an API.
#     See the examples at http://api.django-rest-framework.org to see this in action.
#     """
# 
#     media_type = 'text/html'
#     format = 'html'
#     template = 'search_rank_template.html'
# 
#     def render(self, obj=None, media_type=None):
#         """
#         Renders *obj* using the :attr:`template` specified on the class.
#         """
#         if type(obj) is not dict:
#             return obj
# 
#         template = loader.get_template(self.template)
#         context = RequestContext(self.view.request, obj)
#         return template.render(context)
# 
# 
# 
# class RankChartHtmlRenderer(ChartTemplateRenderer):
#     """
#     Renderer which serializes to JSON
#     """
#     media_type = 'text/html'
#     format = 'html'
#     template = ""
# 
# 
# 
# class KeysChartHtmlRenderer(RankChartHtmlRenderer):
#     """
#     Renderer which serializes to JSON
#     """
#     template = "keywords_itemsrank.html"
# 
# 
# 
# class RankPivotChartHtmlRenderer(RankChartHtmlRenderer):
#     """
#     Renderer which serializes to JSON
#     """
#     template = "keywords_rankstatistic.html"
# 
# 
# 
# class AvgRankPivotChartHtmlRenderer(RankChartHtmlRenderer):
#     """
#     Renderer which serializes to JSON
#     """
#     template = "keywords_itemsrank.html"
# 
# 
# 
# class TradePivotChartHtmlRenderer(RankChartHtmlRenderer):
#     """
#     Renderer which serializes to JSON
#     """
#     template = ""
# 
# 
# 
# class TradeTopChartHtmlRenderer(RankChartHtmlRenderer):
#     """
#     Renderer which serializes to JSON
#     """
#     template = ""
# 
# 
#
