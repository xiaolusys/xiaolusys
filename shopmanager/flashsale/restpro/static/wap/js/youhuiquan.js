/**
 * Created by linjie on 15-7-24.
 */

//将从接口获取的JSON填充到HTML中

var url = "/rest/v1/user/mycoupon/";
$.get(url, function (res) {
    console.log(res);
	if(res.length>0){
    $.each(res, function (i, val) {
        var coupon_no = val.coupon_no;
        var coupon_status = val.coupon_status;
        var coupon_type = val.coupon_type;
        var coupon_user = val.coupon_user;
        var coupon_value = val.coupon_value;
        var deadline = val.deadline;
        var created = val.created;
        if (coupon_value == 3 && coupon_status == 3) {
            var content1 = '<li class="type1">' +
                '<p class="name">全场任意商品满30返3多可叠加</p>' +
                '<p class="date">' + created + '－' + deadline + '</p>' +
                '</li>';
            $(".youxiao").append(content1);
        }
        if (coupon_value == 30 && coupon_status == 3) {
            var content2 = '<li class="type2">' +
                '<p class="name">全场任意商品满300返30多可叠加</p>' +
                '<p class="date">' + created + '－' + deadline + '</p>' +
                '</li>';
            $(".youxiao").append(content2);
        }
        if (coupon_value == 30 && coupon_status == 2) {
            //已经过期的优惠券
            var content3 = '<li class="type3">' +
                '<p class="name">全场任意商品满300返30多可叠加</p>' +
                '<p class="date">' + created + '－' + deadline + '</p>' +
                '</li>';
            $(".shixiao_list").append(content3);

        }
        if (coupon_value == 3 && coupon_status == 2) {
            //已经过期的优惠券
            var content4 = '<li class="type4">' +
                '<p class="name">全场任意商品满30返3多可叠加</p>' +
                '<p class="date">' + created + '－' + deadline + '</p>' +
                '</li>';
            $(".shixiao_list").append(content4);

        }
    });}
	else{
		location.href = '/static/wap/pages/youhuiquan-kong.html';
	}

});
