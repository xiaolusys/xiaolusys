from django.conf.urls import include, url


from . import views

urlpatterns = [
    url(r'^awards/', views.LuckyAwardView.as_view(), name="lucky-awards"),
]
