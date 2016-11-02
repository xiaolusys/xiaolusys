import httplib2
import copy
from django.views.generic import View
from django.http import HttpResponse


class ProxyView(View):
    """docstring for ProxyView"""
    proxy_format = None
    extra_get_params = {}
    extra_post_params = {}

    def request_handler(self, request, url):
        """docstring for request_handler"""
        conn = httplib2.Http()

        params = copy.copy(request.GET)
        params.update(self.get_extra_get_params())
        url_ending = '%s?%s' % (url, params.urlencode())
        url = self.proxy_format % url_ending
        if request.method == 'GET':
            response, content = conn.request(url, request.method)
        elif request.method == 'POST':
            data = copy.copy(request.POST)
            data.update(self.get_extra_post_params())
            response, content = conn.request(url, request.method, data.urlencode(),
                                             headers={'content-type': 'application/x-www-form-urlencoded'})
        content = self.process_response(response, content)
        return HttpResponse(content, status=int(response['status']),
                            content_type=response.get('content-type', response.get('Content-Type', 'text/html')))

    def get_extra_get_params(self):
        """docstring for get_extra_get_params"""
        return self.extra_get_params

    def get_extra_post_params(self):
        """docstring for get_extra_post_params"""
        return self.extra_post_params

    def process_response(self, response, content):
        """docstring for process_response"""
        return content

    get = post = put = request_handler
