from django.conf.urls.defaults    import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .views import PackageByCsvFileView,DiffPackageDataView,PackageWeightView
from .resources import PackageListResource
from .renderers import BaseJsonRenderer,PackageDiffHtmlRenderer,PackageWeightHtmlRenderer
from shopback.base.permissions import IsAuthenticated
from shopback.base.authentication import UserLoggedInAuthentication,login_required_ajax

urlpatterns = patterns('shopapp.yunda.views',

     (r'^impackage/$',PackageByCsvFileView.as_view(
        resource=PackageListResource,
        renderers=(BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),  
                       
    (r'^today/diff/$',DiffPackageDataView.as_view(
        resource=PackageListResource,
        renderers=(BaseJsonRenderer,PackageDiffHtmlRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )), 
                       
    (r'^package/weight/$',PackageWeightView.as_view(
        resource=PackageListResource,
        renderers=(BaseJsonRenderer,PackageWeightHtmlRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),   
)
