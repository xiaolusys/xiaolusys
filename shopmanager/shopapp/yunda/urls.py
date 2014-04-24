from django.conf.urls.defaults    import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .views import PackageByCsvFileView
from .resources import PackageListResource
from shopback.base.renderers  import BaseJsonRenderer
from shopback.base.permissions import IsAuthenticated
from shopback.base.authentication import UserLoggedInAuthentication,login_required_ajax

urlpatterns = patterns('shopapp.yunda.views',

     (r'^impackage/$',PackageByCsvFileView.as_view(
        resource=PackageListResource,
        renderers=(BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),    
)
