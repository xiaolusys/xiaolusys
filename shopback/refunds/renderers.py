# from djangorestframework.renderers import TemplateRenderer
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer


class RefundProductRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to Table
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'refunds/refund_products.html'


class RefundManagerRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to Table
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'refunds/refund_manager.html'
