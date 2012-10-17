from djangorestframework.renderers import TemplateRenderer,JSONRenderer



class PurchaseItemHtmlRenderer(TemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'purchases/purchasemainpage.html'