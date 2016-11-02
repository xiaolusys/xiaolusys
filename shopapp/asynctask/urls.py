from django.conf.urls import patterns, include, url
from django.contrib.admin.views.decorators import staff_member_required

# from core.options.authentication import UserLoggedInAuthentication
# from core.options.permissions import IsAuthenticated
# from shopapp.asynctask.renderers import BaseJsonRenderer,AsyncPrintHtmlRenderer
from shopapp.asynctask.views import (AsyncCategoryView,
                                     AsyncOrderView,
                                     AsyncInvoicePrintView,
                                     AsyncInvoice2PrintView,
                                     AsyncExpressPrintView)

# from shopapp.asynctask.resources import AsyncTaskResource
# from rest_framework import routers
# 
# 
# router = routers.DefaultRouter()
# router_urls = router.urls
# 
# router_urls += patterns('',
#          url(r'^v1/', include(router.urls)),
#          url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))               
#          url(r'^invoice/', AsyncCategoryView.as_view, name="invoice")
#     )

urlpatterns = patterns('',

                       (r'^category/(?P<cids>[^/]+)/$', AsyncCategoryView.as_view(
                           # resource=AsyncTaskResource,
                           # renderers=(BaseJsonRenderer,),
                           # authentication=(UserLoggedInAuthentication,),
                           # permissions=(IsAuthenticated,)
                       )),
                       (r'^orders/(?P<start_dt>[^/]+)/(?P<end_dt>[^/]+)/$', AsyncOrderView.as_view(
                           # resource=AsyncTaskResource,
                           # renderers=(BaseJsonRenderer,),
                           #  authentication=(UserLoggedInAuthentication,),
                           # permissions=(IsAuthenticated,)
                       )),

                       (r'^invoice/$', staff_member_required(AsyncInvoicePrintView.as_view())),
                       (r'^invoice2/$', staff_member_required(AsyncInvoice2PrintView.as_view())),
                       # resource=AsyncTaskResource,
                       # renderers=(AsyncPrintHtmlRenderer,),
                       #  authentication=(UserLoggedInAuthentication,),
                       # permissions=(IsAuthenticated,)
                       # ))),

                       (r'^express/$', staff_member_required(AsyncExpressPrintView.as_view(
                           # resource=AsyncTaskResource,
                           # renderers=(AsyncPrintHtmlRenderer,),
                           # authentication=(UserLoggedInAuthentication,),
                           # permissions=(IsAuthenticated,)
                        ))),
                       )
