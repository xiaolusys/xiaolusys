/**
 * Created by jishu_linjie on 9/24/15.
 */

$("#coupon_release_left").click(function () {
    //领取优惠券
    console.log("150-10");
    //var data = {"coupon_type": "C150_10"};
    //2015-10-8 修改按照优惠券模板来发放
    var data = {"template_id": 5};
    var d = $("#coupon_release_left");
    Action_release(data, d);
});

$("#coupon_release_right").click(function () {
    //领取优惠券
    console.log("259-20");
    //var data = {"coupon_type": "C259_20"};
    //2015-10-8 修改按照优惠券模板来发放
    var data = {"template_id": 6};
    var d = $("#coupon_release_right");
    Action_release(data, d);
});

$("#coupon_release").click(function () {
    //领取优惠券
    console.log("12-12");
    //var data = {"coupon_type": "C259_20"};
    //2015-10-8 修改按照优惠券模板来发放
    var data = {"template_id": 11};
    var d = $("#coupon_release");
    Action_release(data, d);
});

function Action_release(data, d) {
    var url = GLConfig.baseApiUrl + GLConfig.usercoupons;
    if (d.hasClass('loading')) {
        return
    }
    d.addClass("loading");
    $.ajax({
        "url": url,
        "data": data,
        "success": callback,
        "type": "post",
        "csrfmiddlewaretoken": csrftoken,
        error: function (data) {
            console.log('debug profile:', data);
            if (data.status == 403) {
                drawToast('您还没有登陆哦!');
            }
        }
    });
    function callback(res) {
        d.removeClass("loading");
        console.log("debug :", res);
        if (res.res == "success") {
            drawToast("领取成功 赶紧去挑选商品吧 不要过期哦！");
            //等待3秒跳转到优惠券页面
        }
        if (res.res == "already") {
            drawToast("您已经领取优惠券啦 赶紧去挑选商品吧 不要过期哦！");
        }
        if (res.res == "no_type") {
            drawToast("优惠券类型不正确呢！");
        }
        if (res.res == "not_release") {
            drawToast("还没有开放该优惠券哦 敬请期待！");
        }
        if (res.res == "cu_not_fund") {
            drawToast("用户未找到！尝试重新登陆");
        }
        if (res.res == "limit") {
            drawToast("超过领取限制哦~");
        }
    }
}
