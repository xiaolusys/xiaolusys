__author__ = 'meixqhi'
from django.conf.urls import include, url


urlpatterns = [
    url(r'^jd/',include('shopapp.jingdong.urls')),
    url(r'^memorule/',include('shopapp.memorule.urls')),
    # (r'^search/',include('shopapp.collector.urls')),
    url(r'^report/',include('shopapp.report.urls')),
    url(r'^autolist/',include('shopapp.autolist.urls')),
    url(r'^async/',include('shopapp.asynctask.urls')),
    url(r'^calendar/',include('shopapp.calendar.urls')),
    url(r'^comment/',include('shopapp.comments.urls')),
    url(r'^yunda/',include('shopapp.yunda.urls')),
    url(r'^examination/',include('shopapp.examination.urls')),
    url(r'^intercept/',include('shopapp.intercept.urls')),
    url(r'^second_time_sort/',include('shopapp.second_time_sort.urls')),
    url(r'^sample/',include('shopapp.sampleproduct.urls')),
    #(r'^zhongtong/',include('shopapp.zhongtong.urls')),
]

