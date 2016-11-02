from django.conf.urls import patterns, include, url

# from core.options.authentication import UserLoggedInAuthentication
# from core.options.permissions import IsAuthenticated


urlpatterns = patterns('shopapp.report.views',

                       url('reportform/$', 'gen_report_form_file', name='gen_report_form_file'),
                       )
