from django.http import HttpResponse,HttpResponseRedirect
from django.conf import settings

def loginJD(request):
    
    return HttpResponseRedirect(
        '&'.join(['%s?'%settings.JD_AUTHRIZE_URL,
                 'response_type=code',
                 'client_id=%s'%settings.JD_APP_KEY,
                 'redirect_uri=%s'%settings.JD_REDIRECT_URI,
                 'state=jingdong']))
    
def loginAuthJD(request):
    print request.REQUEST
    
    return HttpResponse('success')