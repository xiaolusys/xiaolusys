# coding:utf-8
from django.conf.urls import include, url
from flashsale.dinghuo import views
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .views import DailyStatsView, ChangeDetailView, StatsByProductIdView, DailyWorkView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [

    url(r'^searchproduct/$', views.search_product, name='searchProduct'),       #搜索所有的商品 ajax
    url(r'^initdraft/$', views.init_draft, name='init_draft'),                   #初始化草稿箱
    url(r'^dingdan/$', views.new_order, name="new_order"),                     #订单页面填写完成后跳转
    url(r'^delcaogao/$', views.del_draft, name="delcaogao"),                   #删除所有草稿
    url(r'^test/$', views.test, name="test"),                                  #测试用
    url(r'^adddetail/$', views.add_purchase, name="adddetail"),                 #从商品界面做跳转 暂时没有用
    url(r'^test/(?P<id>\d+)/(?P<name>\d+)/(?P<sex>\d+)/$', views.test, name="test"),#无作用
    url(r'^plusquantity/$', views.plus_quantity, name="plusquantity"),          #增加草稿里面的一个商品的数量
    url(r'^plusordertail/$', views.plusordertail, name="plusordertail"),          #增加订单详情里面的一个商品的数量
    url(r'^minusordertail/$', views.minusordertail, name="minusordertail"),          #减少订单详情里面的一个商品的数量
    url(r'^minusarrivedquantity/$', views.minusarrived, name="minusarrivedquantity"),          #减少
    url(r'^minusquantity/$', views.minusquantity, name="minusquantity"),       #减少草稿里面的一个商品的数量
    url(r'^removedraft/$', views.removedraft, name="removedraft"),             #删除草稿里面的一个商品
    url(r'^detail/(?P<orderdetail_id>\d+)/$', views.viewdetail, name="mydetail"),
    url(r'^detaillayer/(?P<orderdetail_id>\d+)/$', views.detaillayer, name="detaillayer"),
    url(r'^changestatus/$', views.changestatus, name="changestatus"),
    url(r'^changedetail/(?P<order_detail_id>\d+)/$',csrf_exempt(staff_member_required(ChangeDetailView.as_view())), name="changedetail"),
    url(r'^daily/', staff_member_required(DailyStatsView.as_view()), name="dailystats"),  #大货每天统计
    url(r'^changearrivalquantity/$', views.changearrivalquantity, name="changearrivalquantity"),
    url(r'^statsbypid/(?P<product_id>\d+)/$', staff_member_required(StatsByProductIdView.as_view()), name="statsbypid"),  #根据商品id统计大货
    url(r'^dailywork/', staff_member_required(DailyWorkView.as_view()), name="dailywork"),  #大货任务
    url(r'^changememo/$', views.change_memo, name="changeMemo"),
    url(r'^setusertogroup/$', views.setusertogroup, name="setusertogroup"),
    url(r'^adddetailtodinghuo/$', views.add_detail_to_ding_huo, name="add_detail_to_ding_huo"),
    url(r'^changeorderlist/$', views.modify_order_list, name="modify_order_list"),

]
