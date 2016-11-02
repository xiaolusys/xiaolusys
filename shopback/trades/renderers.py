# from djangorestframework.renderers import TemplateRenderer
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer


class CheckOrderRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to Table
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'trades/New_check_order.html'


class ReviewOrderRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to Table
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'trades/review_order_template.html'


class ExchangeOrderRender(TemplateHTMLRenderer):
    """
    Renderer which serializes to Table
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'trades/exchanges_template.html'


# class ExchangeOrderRender(TemplateRenderer):
#     """
#     Renderer which serializes to Table
#     """
#     
#     media_type = 'text/html'
#     format = 'html'
#     template = 'trades/exchanges_template.html'    
class DirectOrderRender(TemplateHTMLRenderer):
    """
    Renderer which serializes to Table
    """

    media_type = 'text/html'
    format_name = 'html'
    template_name = 'trades/direct_trade_template.html'


class StatisticMergeOrderRender(TemplateHTMLRenderer):
    """
    Renderer which serializes to Table
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'trades/trade_products_statistic.html'


class StatisticMergeOrderAsyncRender(TemplateHTMLRenderer):
    """
    Renderer which serializes to Table
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'trades/trade_products_statistic_async.html'


class StatisticOutStockRender(TemplateHTMLRenderer):
    """
    Renderer which serializes to Table
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'trades/out_stock_statistic.html'


class OrderListRender(TemplateHTMLRenderer):
    """
    Renderer which serializes to Table
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'trades/trade_order_list.html'


class TradeLogisticRender(TemplateHTMLRenderer):
    """
    Renderer which serializes to Table
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'trades/trade_logistic_detail.html'


class RelatedOrderRenderer(TemplateHTMLRenderer):
    """
    Renderer which serializes to Table
    """

    media_type = 'text/html'
    format = 'html'
    template_name = 'related_orders_template.html'
