__author__ = 'meixqhi'
from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    
    (r'^jd/',include('shopapp.jingdong.urls')),
    (r'^memorule/',include('shopapp.memorule.urls')),
    (r'^search/',include('shopapp.collector.urls')),
    (r'^report/',include('shopapp.report.urls')),
    (r'^autolist/',include('shopapp.autolist.urls')),
    (r'^async/',include('shopapp.asynctask.urls')),
    (r'^calendar/',include('shopapp.calendar.urls')),
    (r'^comment/',include('shopapp.comments.urls')),
    (r'^yunda/',include('shopapp.yunda.urls')),
    (r'^examination/',include('shopapp.examination.urls')),
    (r'^intercept/',include('shopapp.intercept.urls')),
    (r'^second_time_sort/',include('shopapp.second_time_sort.urls')),
    (r'^sample/',include('shopapp.sampleproduct.urls')),
    #(r'^zhongtong/',include('shopapp.zhongtong.urls')),
)

