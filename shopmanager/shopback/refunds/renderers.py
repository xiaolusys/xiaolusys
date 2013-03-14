from djangorestframework.renderers import TemplateRenderer


class RefundProductRenderer(TemplateRenderer):
    """
    Renderer which serializes to Table
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'refunds/refund_products.html'