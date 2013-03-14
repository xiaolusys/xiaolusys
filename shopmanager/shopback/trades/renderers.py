from djangorestframework.renderers import TemplateRenderer


class CheckOrderRenderer(TemplateRenderer):
    """
    Renderer which serializes to Table
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'trades/check_order_template.html'
    
    
class ReviewOrderRenderer(TemplateRenderer):
    """
    Renderer which serializes to Table
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'trades/review_order_template.html'
    
    
class ExchangeOrderRender(TemplateRenderer):
    """
    Renderer which serializes to Table
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'trades/exchanges_template.html'
    
    
class StatisticMergeOrderRender(TemplateRenderer):
    """
    Renderer which serializes to Table
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'trades/trade_products_statistic.html'
    
    
class StatisticOutStockRender(TemplateRenderer):
    """
    Renderer which serializes to Table
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'trades/out_stock_statistic.html'    