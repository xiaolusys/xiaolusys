from djangorestframework.renderers import TemplateRenderer


class CheckOrderRenderer(TemplateRenderer):
    """
    Renderer which serializes to Table
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'trades/check_order_template.html'
    
    
class ReviewOrderRenderer(TemplateRenderer):
    """
    Renderer which serializes to Table
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'trades/review_order_template.html'