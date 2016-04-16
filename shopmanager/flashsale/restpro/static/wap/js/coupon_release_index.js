/**
 * Created by jishu_linjie on 9/24/15.
 */
var CLICK_COUPON_TIMES = 1;


function Action_release(data, d) {
    var url = GLConfig.baseApiUrl + GLConfig.usercoupons;

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
        console.log('res --->: ',res);
        drawToast(res.res);
    //    if (res.res == "success") {
    //        drawToast("领取成功 赶紧去挑选商品吧 ！");
    //        //等待3秒跳转到优惠券页面
    //    }
    //    if (res.res == "already") {
    //        drawToast("您已经领取优惠券啦 赶紧去挑选商品吧 ！");
    //    }
    //    if (res.res == "no_type") {
    //        drawToast("还没有开放该优惠券敬请期待！");
    //    }
    //    if (res.res == "not_release") {
    //        drawToast("还没有开放该优惠券哦 敬请期待！");
    //    }
    //    if (res.res == "cu_not_fund") {
    //        drawToast("用户未找到！尝试重新登陆");
    //    }
    //    if (res.res == "limit") {
    //        drawToast("您已经领取过了哦~");
    //    }
    }
}

function Set_coupon_tpls() {
    var tpls_url = GLConfig.baseApiUrl + GLConfig.coupon_tpls;
    $.ajax({
        "url": tpls_url,
        "data": {},
        "success": callback,
        "type": "get",
        "csrfmiddlewaretoken": csrftoken
    });
    function callback(res) {
        var img_num = 0;
        if (res.length > 0) {
            var html = '<div>' +
                '<div class="glist_cou" id="coupon_release" onclick="clickRelease();"><ul id="tpl_ul_show"></ul></div>' +
                '<script type="text/html" id="coupon_tpl"><li cid="{{ id }}"><img src="{{ post_img }}"></li></script>' +
                '</div>';
            $(".fixed-nav").after(html);
        }
        $.each(res, function (i, v) {
            if (v.post_img != "") {
                var tplhml = create_tpl_show(v);
                $("#tpl_ul_show").append(tplhml);
                img_num += 1;
            }
        });
        // 调用轮播
        var autoplay = false;
        if (img_num > 1) {
            autoplay = false; //优惠券张数大于1的时候显示轮播（true） 暂时不设轮播
        }
        else if (img_num <= 0) {
            $(".glist_cou").remove();//没有优惠券的时候删除dom
        }
        CouponTemplateShow($(".glist_cou"), 500, 3000, autoplay);
    }

    function create_tpl_show(obj) {
        var copl = $("#coupon_tpl").html();
        return hereDoc(copl).template(obj)
    }
}

function CouponTemplateShow(dom, speed, delay, autoplay) {
    $(dom).unslider({
        autoplay: autoplay,
        speed: speed,
        delay: delay,
        keys: false,
        arrows: false,
        nav: false
    });
}

function clickRelease() {

    //领取优惠券
    console.log(123);
    if (CLICK_COUPON_TIMES > 1) {
        // 第二次点击跳转到优惠券页面
        location.href = "pages/youhuiquan.html";
    }
    var uldom = $("#tpl_ul_show");
    $.each($(uldom).children(), function (i, v) {
        var tmpid = $(v).attr("cid");
        var data = {"template_id": tmpid};
        var d = $("#coupon_release");
        console.log("data :", data);
        Action_release(data, d);
    });
    CLICK_COUPON_TIMES += 1; // 再次点击
}

//console.log(123);
//$(document).ready(
//    function () {
//        console.log(123123);
//        $("#coupon_release").click(function () {
//            //领取优惠券
//            console.log(123);
//            if (CLICK_COUPON_TIMES > 1) {
//                // 第二次点击跳转到优惠券页面
//                location.href = "pages/youhuiquan.html";
//            }
//            var uldom = $("#tpl_ul_show");
//            $.each($(uldom).children(), function (i, v) {
//                var tmpid = $(v).attr("cid");
//                var data = {"template_id": tmpid};
//                var d = $("#coupon_release");
//                console.log("data :", data);
//                Action_release(data, d);
//            });
//            CLICK_COUPON_TIMES += 1; // 再次点击
//        });
//    }
//);
