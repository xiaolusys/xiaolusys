from django.conf.urls import include, url
from django.views.generic import TemplateView

from games.paint.views import CreateAccountView

urlpatterns = [
    url(r'^createaccount/$', CreateAccountView.as_view(), name='paint_create_account'),
]
