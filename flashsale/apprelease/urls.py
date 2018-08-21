# coding=utf-8

from django.conf.urls import url
import views

urlpatterns = [
    url(r'newversion', views.AppReleaseView.as_view(), name="app_release_newest"),
    url(r'^add/$', views.addNewReleaseView.as_view(), name="add_new_release"),
]
