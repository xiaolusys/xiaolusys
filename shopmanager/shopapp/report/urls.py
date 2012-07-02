from django.conf.urls.defaults import patterns, include, url
from shopback.base.authentication import UserLoggedInAuthentication
from shopback.base.permissions import IsAuthenticated


urlpatterns = patterns('shopapp.report.views',

    url('reportform/$','gen_report_form_file',name='gen_report_form_file'),

)


  