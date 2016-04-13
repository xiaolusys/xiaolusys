# __author__ = 'meixqhi'
# import json
# from django.core.serializers.json import DjangoJSONEncoder
# from djangorestframework.renderers import JSONRenderer ,TemplateRenderer
# from djangorestframework.utils.mediatypes import get_media_type_params
# from django.template import RequestContext, loader
# from djangorestframework.renderers import JSONRenderer ,TemplateRenderer
# from djangorestframework.utils.mediatypes import get_media_type_params
# from chartit import Chart,PivotChart
# 
# class ChartJSONRenderer(JSONRenderer):
#     """
#     Renderer which serializes to JSON
#     """
#     media_type = 'application/json'
#     format = 'json'
# 
#     def render(self, obj=None, media_type=None):
#         """
#         Renders *obj* into serialized JSON.
#         """
# 
#         if type(obj) is dict:
#             obj = {"code":0,"response_content":obj}
#         else:
#             obj = {"code":1,"response_error":obj}
# 
#         class ChartEncoder(json.JSONEncoder):
#             def default(self, obj):
#                 if isinstance(obj, (Chart,PivotChart)):
#                     return obj.hcoptions #Serializer().serialize
#                 return DjangoJSONEncoder.default(self, obj)
# 
#         # If the media type looks like 'application/json; indent=4', then
#         # pretty print the result.
#         indent = get_media_type_params(media_type).get('indent', None)
#         sort_keys = False
#         try:
#             indent = max(min(int(indent), 8), 0)
#             sort_keys = True
#         except (ValueError, TypeError):
#             indent = None
# 
#         return json.dumps(obj, cls=ChartEncoder, indent=indent, sort_keys=sort_keys)
# 
# 
# class ChartTemplateRenderer(TemplateRenderer):
# 
#     media_type = 'text/html'
#     format = 'chart'
#     template = "chart_render_template.html"
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
# class BaseJsonRenderer(JSONRenderer):
#     """
#     Renderer which serializes to JSON
#     """
#     media_type = 'application/json'
#     format = 'json'
# 
#     def render(self, obj=None, media_type=None):
#         """
#         Renders *obj* into serialized JSON.
#         """
#         if isinstance(obj,(list,tuple,)):
#             obj = {"code":0,"response_content":obj}
#         elif isinstance(obj,dict) and (obj.has_key('code') or obj.has_key('field-errors')
#                                        or obj.has_key('errors') or obj.has_key('errcode')):
#             pass
#         elif isinstance(obj,dict):
#             obj = {"code":0,"response_content":obj}
#         else:
#             obj = {"code":1,"response_error":obj}
# 
#         # If the media type looks like 'application/json; indent=4', then
#         # pretty print the result.
#         indent = get_media_type_params(media_type).get('indent', None)
#         sort_keys = False
#         try:
#             indent = max(min(int(indent), 8), 0)
#             sort_keys = True
#         except (ValueError, TypeError):
#             indent = None
# 
#         return json.dumps(obj, cls=DjangoJSONEncoder, indent=indent, sort_keys=sort_keys)
#   
#   
#
