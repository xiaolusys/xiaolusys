import re
import time
import datetime
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View


class FrozenScoreView(View):
    
    def get(self, request, *args, **kwargs):
        content = request.REQUEST
        mobile = content.get('mobile','0')
        openid = content.get('openid',None)
    
        
        response = {"code":"good", "verifycode":""}
        return HttpResponse(json.dumps(response),mimetype='application/json')
