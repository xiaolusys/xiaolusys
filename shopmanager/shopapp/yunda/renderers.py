from djangorestframework.renderers import TemplateRenderer,JSONRenderer
from shopback.base.renderers  import BaseJsonRenderer


class PackageDiffHtmlRenderer(TemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'yunda/diff_small_parent_package.html'
    
    

class PackageWeightHtmlRenderer(TemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'yunda/weight_small_package.html' 
    


