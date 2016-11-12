__author__ = "kaineng.fang"

import json
from django.utils import six
from django.core.exceptions import ImproperlyConfigured
from django.http.multipartparser import parse_header
from django.template import Context, RequestContext, loader, Template
from django.core.serializers.json import DjangoJSONEncoder

from rest_framework.compat import SHORT_SEPARATORS, LONG_SEPARATORS, INDENT_SEPARATORS
from rest_framework.settings import api_settings
from rest_framework.utils import encoders
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer


class new_BaseJSONRenderer(JSONRenderer):
    """
    Renderer which serializes to JSON.
    """

    media_type = 'application/json'
    format = 'json'
    encoder_class = encoders.JSONEncoder
    ensure_ascii = not api_settings.UNICODE_JSON
    compact = api_settings.COMPACT_JSON

    # We don't set a charset because JSON is a binary encoding,
    # that can be encoded as utf-8, utf-16 or utf-32.
    # See: http://www.ietf.org/rfc/rfc4627.txt
    # Also: http://lucumr.pocoo.org/2013/7/19/application-mimetypes-and-encodings/
    charset = None

    def get_indent(self, accepted_media_type, renderer_context):
        if accepted_media_type:
            # If the media type looks like 'application/json; indent=4',
            # then pretty print the result.
            # Note that we coerce `indent=0` into `indent=None`.
            base_media_type, params = parse_header(accepted_media_type.encode('ascii'))
            try:
                return zero_as_none(max(min(int(params['indent']), 8), 0))
            except (KeyError, ValueError, TypeError):
                pass

        # If 'indent' is provided in the context, then pretty print the result.
        # E.g. If we're being called by the BrowsableAPIRenderer.
        return renderer_context.get('indent', None)

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON, returning a bytestring.
        """
        if isinstance(data, (list, tuple,)):
            data = {"code": 0, "response_content": data}
        elif isinstance(data, dict) and (data.has_key('code') or data.has_key('field-errors')
                                         or data.has_key('errors') or data.has_key('errcode')):
            pass
        elif isinstance(data, dict):
            data = {"code": 0, "response_content": data}
        else:
            data = {"code": 1, "response_error": data}

        renderer_context = renderer_context or {}
        indent = self.get_indent(accepted_media_type, renderer_context)

        if indent is None:
            separators = SHORT_SEPARATORS if self.compact else LONG_SEPARATORS
        else:
            separators = INDENT_SEPARATORS

        ret = json.dumps(
            data, cls=self.encoder_class,
            indent=indent, ensure_ascii=self.ensure_ascii,
            separators=separators
        )

        # On python 2.x json.dumps() returns bytestrings if ensure_ascii=True,
        # but if ensure_ascii=False, the return type is underspecified,
        # and may (or may not) be unicode.
        # On python 3.x json.dumps() returns unicode strings.
        if isinstance(ret, six.text_type):
            # We always fully escape \u2028 and \u2029 to ensure we output JSON
            # that is a strict javascript subset. If bytes were returned
            # by json.dumps() then we don't have these characters in any case.
            # See: http://timelessrepo.com/json-isnt-a-javascript-subset
            ret = ret.replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
            return bytes(ret.encode('utf-8'))
        return ret


def zero_as_none(value):
    return None if value == 0 else value


##
class new_ChartJSONRenderer(JSONRenderer):
    """
    Renderer which serializes to JSON.
    """

    media_type = 'application/json'
    format = 'json'
    encoder_class = encoders.JSONEncoder
    ensure_ascii = not api_settings.UNICODE_JSON
    compact = api_settings.COMPACT_JSON

    # We don't set a charset because JSON is a binary encoding,
    # that can be encoded as utf-8, utf-16 or utf-32.
    # See: http://www.ietf.org/rfc/rfc4627.txt
    # Also: http://lucumr.pocoo.org/2013/7/19/application-mimetypes-and-encodings/
    charset = None

    def get_indent(self, accepted_media_type, renderer_context):
        if accepted_media_type:
            # If the media type looks like 'application/json; indent=4',
            # then pretty print the result.
            # Note that we coerce `indent=0` into `indent=None`.
            base_media_type, params = parse_header(accepted_media_type.encode('ascii'))
            try:
                return zero_as_none(max(min(int(params['indent']), 8), 0))
            except (KeyError, ValueError, TypeError):
                pass

        # If 'indent' is provided in the context, then pretty print the result.
        # E.g. If we're being called by the BrowsableAPIRenderer.
        return renderer_context.get('indent', None)

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON, returning a bytestring.
        """
        if type(data) is dict:
            data = {"code": 0, "response_content": data}
        else:
            data = {"code": 1, "response_error": data}

        class ChartEncoder(json.JSONEncoder):
            pass
            # def default(self, data):
            #     if isinstance(data, (Chart, PivotChart)):
            #         return data.hcoptions  # Serializer().serialize
            #     return DjangoJSONEncoder.default(self, data)

        renderer_context = renderer_context or {}
        indent = self.get_indent(accepted_media_type, renderer_context)

        if indent is None:
            separators = SHORT_SEPARATORS if self.compact else LONG_SEPARATORS
        else:
            separators = INDENT_SEPARATORS

        ret = json.dumps(
            data, cls=self.encoder_class,
            indent=indent, ensure_ascii=self.ensure_ascii,
            separators=separators
        )

        # On python 2.x json.dumps() returns bytestrings if ensure_ascii=True,
        # but if ensure_ascii=False, the return type is underspecified,
        # and may (or may not) be unicode.
        # On python 3.x json.dumps() returns unicode strings.
        if isinstance(ret, six.text_type):
            # We always fully escape \u2028 and \u2029 to ensure we output JSON
            # that is a strict javascript subset. If bytes were returned
            # by json.dumps() then we don't have these characters in any case.
            # See: http://timelessrepo.com/json-isnt-a-javascript-subset
            ret = ret.replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
            return bytes(ret.encode('utf-8'))
        return ret


####
class new_ChartTemplateRenderer(TemplateHTMLRenderer):
    media_type = 'text/html'
    format = 'chart'
    template_name = "chart_render_template.html"
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

# Note, subclass TemplateHTMLRenderer simply for the exception behavior
