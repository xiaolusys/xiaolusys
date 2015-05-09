# coding:utf-8
from django.conf.urls import include, url
from flashsale.dinghuo import views

urlpatterns = [
    # Examples:
    # url(r'^$', 'flashsale.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^add/', views.orderadd, name="orderadd"),  #添加商品到订单 测试用
    # url(r'^add/',  views.add, name="addorder"),
    # url(r'^delorder/(?P<del_id>\d+)',  views.delorder, name="delorder"),
    # url(r'^update/(?P<modify_id>\d+)', views.update, name="updateorder"),
    # url(r'^login/', views.login, name="login"),
    # url(r'^logout/', views.logout, name='logout'),
    # url(r'^register/$', views.regist, name='register'),
    # url(r'^detail/(?P<detail_id>\d+)', views.detail, name='orderdetail'),
    # url(r'^addorderitem/$', views.addorderitem, name='addorderitem'),
    # url(r'^ajax_deal/$', views.ajax_index, name="test-ajax"),
    # url(r'^ajax_list/$', views.ajax_list, name='ajax-list'),
    url(r'^checkorderexist/$', views.CheckOrderExist, name='CheckOrderExist'), #检查当前order是否已经存在 ajax
    url(r'^searchproduct/$', views.searchProduct, name='searchProduct'),       #搜索所有的商品 ajax
    url(r'^initdraft/$', views.initdraft, name='initdraft'),                   #初始化草稿箱
    url(r'^dingdan/$', views.neworder, name="adddingdan"),                     #订单页面填写完成后跳转
    url(r'^delcaogao/$', views.delcaogao, name="delcaogao"),                   #删除所有草稿
    url(r'^test/$', views.test, name="test"),                                  #测试用
    url(r'^adddetail/$', views.addpurchase, name="adddetail"),                 #从商品界面做跳转 暂时没有用
    url(r'^test/(?P<id>\d+)/(?P<name>\d+)/(?P<sex>\d+)/$', views.test, name="test"),#无作用
    url(r'^plusquantity/$', views.plusquantity, name="plusquantity"),          #增加草稿里面的一个商品的数量
    url(r'^minusquantity/$', views.minusquantity, name="minusquantity"),       #减少草稿里面的一个商品的数量
    url(r'^removedraft/$', views.removedraft, name="removedraft"),             #删除草稿里面的一个商品
    url(r'^detail/(?P<orderdetail_id>\d+)/$', views.viewdetail, name="mydetail"),
    url(r'^changestatus/$', views.changestatus, name="changestatus"),



]
