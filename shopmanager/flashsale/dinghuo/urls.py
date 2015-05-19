# coding:utf-8
from django.conf.urls import include, url
from flashsale.dinghuo import views
from django.contrib.auth.decorators import login_required
from .views import dailystatsview


urlpatterns = [

    url(r'^add/', views.orderadd, name="orderadd"),  #添加商品到订单 测试用
    url(r'^checkorderexist/$', views.CheckOrderExist, name='CheckOrderExist'), #检查当前order是否已经存在 ajax
    url(r'^searchproduct/$', views.searchProduct, name='searchProduct'),       #搜索所有的商品 ajax
    url(r'^initdraft/$', views.initdraft, name='initdraft'),                   #初始化草稿箱
    url(r'^dingdan/$', views.neworder, name="adddingdan"),                     #订单页面填写完成后跳转
    url(r'^delcaogao/$', views.delcaogao, name="delcaogao"),                   #删除所有草稿
    url(r'^test/$', views.test, name="test"),                                  #测试用
    url(r'^adddetail/$', views.addpurchase, name="adddetail"),                 #从商品界面做跳转 暂时没有用
    url(r'^test/(?P<id>\d+)/(?P<name>\d+)/(?P<sex>\d+)/$', views.test, name="test"),#无作用
    url(r'^plusquantity/$', views.plusquantity, name="plusquantity"),          #增加草稿里面的一个商品的数量
    url(r'^plusordertail/$', views.plusordertail, name="plusordertail"),          #增加订单详情里面的一个商品的数量
    url(r'^minusordertail/$', views.minusordertail, name="minusordertail"),          #减少订单详情里面的一个商品的数量
    url(r'^minusquantity/$', views.minusquantity, name="minusquantity"),       #减少草稿里面的一个商品的数量
    url(r'^removedraft/$', views.removedraft, name="removedraft"),             #删除草稿里面的一个商品
    url(r'^detail/(?P<orderdetail_id>\d+)/$', views.viewdetail, name="mydetail"),
    url(r'^changestatus/$', views.changestatus, name="changestatus"),
    url(r'^changedetail/(?P<orderdetail_id>\d+)/$', views.changedetail, name="changedetail"),
    url(r'^daily/', login_required(dailystatsview.as_view()), name="dailystats"),

]
