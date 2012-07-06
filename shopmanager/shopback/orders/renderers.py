from shopback.base.renderers import ChartTemplateRenderer


class OrderNumPiovtChartHtmlRenderer(ChartTemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    media_type = 'text/html'
    format = 'html'
    template = ''
