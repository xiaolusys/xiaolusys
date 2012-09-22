from djangorestframework.renderers import TemplateRenderer,JSONRenderer



class ProductListHtmlRenderer(TemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'items/itemmainpage.html'