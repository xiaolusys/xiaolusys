from djangorestframework.renderers import TemplateRenderer
from shopback.base.renderers import ChartTemplateRenderer


class TimerOrderStatChartRenderer(ChartTemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'trades/timer_order_statistic_chart.html'
    
    
class ProductOrderTableRenderer(ChartTemplateRenderer):
    """
    Renderer which serializes to Table
    """
    
    media_type = 'text/html'
    format = 'table'
    template = 'product_pivottable.html'
    
    
class RelatedOrderRenderer(TemplateRenderer):
    """
    Renderer which serializes to Table
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'related_orders_template.html'
    
class RefundOrderRenderer(TemplateRenderer):
    """
    Renderer which serializes to Table
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'refund_orders_template.html'

