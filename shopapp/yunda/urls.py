from django.conf.urls import include, url
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView
from shopapp.yunda.views import *
# from .resources import (PackageListResource,
#                         LogisticOrderResource,
#                         BranchZoneResource)
# # from .renderers import BaseJsonRenderer,PackageDiffHtmlRenderer
# from core.options.permissions import IsAuthenticated
from shopback.base.authentication import login_required_ajax

urlpatterns = [
    url(r'^impackage/$', PackageByCsvFileView.as_view(
       # resource=PackageListResource,
       #  renderers=(BaseJsonRenderer,),
       # authentication=(UserLoggedInAuthentication,),
       # permissions=(IsAuthenticated,)
    )),
    url(r'^today/push/$', DiffPackageDataView.as_view(
       # resource=PackageListResource,
       # renderers=(BaseJsonRenderer,PackageDiffHtmlRenderer),
       # authentication=(UserLoggedInAuthentication,),
       #  permissions=(IsAuthenticated,)
    )),
    url(r'package/weight/$', staff_member_required(TemplateView.as_view(
       template_name='yunda/weight_small_package.html'))),
    url(r'^package/$', PackageWeightView.as_view(
       # resource=LogisticOrderResource,
       # renderers=(BaseJsonRenderer,),
       # authentication=(UserLoggedInAuthentication,),
       #  permissions=(IsAuthenticated,)
    )),
    url(r'^order/upload/$', CustomerPackageImportView.as_view(
       # resource=PackageListResource,
       # renderers=(BaseJsonRenderer,),
       # authentication=(UserLoggedInAuthentication,),
       # permissions=(IsAuthenticated,)
    )),
    url (r'^branchzone/$', cache_page(24 * 60 * 60)(BranchZoneView.as_view(
       # resource=BranchZoneResource,
       # renderers=(BaseJsonRenderer,),
       #        authentication=(UserLoggedInAuthentication,),##yuanlai   ##you fang
       #        permissions=(IsAuthenticated,)   ##yuanlai ##
    ))),
]
