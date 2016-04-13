# coding: utf-8

from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer


class ProductListHtmlRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to JSON
    """

    media_type = 'text/html'
    format = 'html'
    # template_name = 'items/itemmainpage.html'
    template_name = 'items/new_itemmainpage.html'


class ProductItemHtmlRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to JSON
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'items/productitemspage.html'


class ProductUpdateHtmlRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to JSON
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'items/productupdate.html'


class ProductSkuHtmlRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to JSON
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'items/productskutable.html'


class ProductHtmlRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to JSON
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'items/product_detail.html'


class ProductDistrictHtmlRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to JSON
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'items/product_district_page.html'


class ProductBarcodeHtmlRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to JSON
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'items/product_barcode_page.html'


class ProductWarnHtmlRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to JSON
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'items/product_stock_warn.html'


class ProductSaleHtmlRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to JSON
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'items/product_sale_stat.html'


class ProductSaleAsyncHtmlRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to JSON
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'items/product_sale_stat_async.html'


class ProductScanRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to JSON
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'items/items_storage_scan.html'
