from djangorestframework.renderers import TemplateRenderer,JSONRenderer



class ProductListHtmlRenderer(TemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'items/itemmainpage.html'
    
    

class ProductItemHtmlRenderer(TemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'items/productitemspage.html'
    
    
    
class ProductUpdateHtmlRenderer(TemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'items/productupdate.html'
    
    
class ProductSkuHtmlRenderer(TemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'items/productskutable.html'
    
    
class ProductHtmlRenderer(TemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'items/product_detail.html'
    
class ProductDistrictHtmlRenderer(TemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'items/product_district_page.html'
    

class ProductBarcodeHtmlRenderer(TemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'items/product_barcode_page.html'
    
    
class ProductWarnHtmlRenderer(TemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'items/product_stock_warn.html'
    

    
class ProductSaleHtmlRenderer(TemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'items/product_sale_stat.html'


    


