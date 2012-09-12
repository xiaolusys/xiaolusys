from djangorestframework.renderers import TemplateRenderer
from shopback.base.renderers import ChartTemplateRenderer


class OrderNumPiovtChartHtmlRenderer(ChartTemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = ''
    
    
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
