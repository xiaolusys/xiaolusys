# from djangorestframework.renderers import TemplateRenderer
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer

class ReviewOrderRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to Table
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'warehouse/review_package_template.html'
