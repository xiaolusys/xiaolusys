# from djangorestframework.renderers import TemplateRenderer,JSONRenderer
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer


class PurchaseItemHtmlRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to HTML
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'purchases/'


class PurchaseHtmlRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to HTML
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'purchases/purchase_page.html'


class PurchaseStorageHtmlRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to HTML
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'purchases/purchase_storage_page.html'


class StorageDistributeRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to HTML
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'purchases/distribute_purchase_storage.html'


class PurchaseShipStorageRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to HTML
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'purchases/ship_storage_page.html'


class PurchasePaymentRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to HTML
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'purchases/purchase_payment_page.html'


class PaymentDistributeRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to HTML
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'purchases/apply_payment_page.html'
