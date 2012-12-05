# Create your views here.
from django.http import HttpResponse
from django.utils.encoding import smart_unicode
from django.utils import simplejson

from contry.models import Municipality

class JSONResponse(HttpResponse):
    def __init__(self, data):
        super(JSONResponse, self).__init__(
                simplejson.dumps(data), mimetype='application/json')

def municipalities_for_county(request):
    if request.is_ajax() and request.GET and 'county_id' in request.GET:
        objs = Municipality.objects.filter(county=request.GET['county_id'])
        return JSONResponse([{'id': o.id, 'name': smart_unicode(o)}
            for o in objs])
    else:
        return JSONResponse({'error': 'Not Ajax or no GET'})
