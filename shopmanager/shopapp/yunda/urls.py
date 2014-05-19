from django.conf.urls.defaults    import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic import TemplateView
from .views import PackageByCsvFileView,DiffPackageDataView,PackageWeightView,CustomerPackageImportView
from .resources import PackageListResource,LogisticOrderResource
from .renderers import BaseJsonRenderer,PackageDiffHtmlRenderer
from shopback.base.permissions import IsAuthenticated
from shopback.base.authentication import UserLoggedInAuthentication,login_required_ajax

urlpatterns = patterns('shopapp.yunda.views',

     (r'^impackage/$',PackageByCsvFileView.as_view(
        resource=PackageListResource,
        renderers=(BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),  
                       
    (r'^today/push/$',DiffPackageDataView.as_view(
        resource=PackageListResource,
        renderers=(BaseJsonRenderer,PackageDiffHtmlRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )), 
                       
    (r'package/weight/$',staff_member_required(TemplateView.as_view(
                        template_name='yunda/weight_small_package.html'))),   
                                       
    (r'^package/$',PackageWeightView.as_view(
        resource=LogisticOrderResource,
        renderers=(BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )), 
                       
    (r'^order/upload/$',CustomerPackageImportView.as_view(
        resource=PackageListResource,
        renderers=(BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),  
)
