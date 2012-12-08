from djangorestframework.renderers import TemplateRenderer


class CheckOrderRenderer(TemplateRenderer):
    """
    Renderer which serializes to Table
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'trades/check_order_template.html'