from djangorestframework.renderers import TemplateRenderer
from shopback.base.renderers  import BaseJsonRenderer


class AsyncPrintHtmlRenderer(TemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'asynctask/async_print_commit.html'