# from djangorestframework.renderers import TemplateRenderer
from shopback.base.new_renders import new_ChartTemplateRenderer
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer


class TimerOrderStatChartRenderer(new_ChartTemplateRenderer):
    """
    Renderer which serializes to JSON
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'trades/order_report_chart.html'


class ProductOrderTableRenderer(new_ChartTemplateRenderer):
    """
    Renderer which serializes to Table
    """

    media_type = 'text/html'
    format = 'table'
    template_name = 'product_pivottable.html'


class RelatedOrderRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to Table
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'related_orders_template.html'


class RefundOrderRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to Table
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'refund_orders_template.html'
