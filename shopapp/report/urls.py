from django.conf.urls import include, url

# from core.options.authentication import UserLoggedInAuthentication
# from core.options.permissions import IsAuthenticated
from shopapp.report.views import *

urlpatterns = [
    url('reportform/$', gen_report_form_file, name='gen_report_form_file'),
]
