from djangorestframework.renderers import TemplateRenderer,JSONRenderer
from shopback.base.renderers  import BaseJsonRenderer


class PackageDiffHtmlRenderer(TemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'yunda/upload_yunda_package.html'
    
    

    


