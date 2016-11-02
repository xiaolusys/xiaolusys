/**
 * Created by linjie on 15-7-24.
 */

$(document).ready(function () {


    var url = GLConfig.baseApiUrl + GLConfig.usercoupons;
    var nums = 0;
    $.get(url, function (res) {
        console.log(res);
        if (res.length > 0) {

            $.each(res, function (i, val) {
                if (val.coupon_status == 3) {
                    nums = nums + 1;//有效可用的优惠券数量
                }
            });
            if (nums == 0) {
                //$(".tips").empty().append("亲，暂无优惠券派发，敬请期待吧~");
            }
            else {
                var tips_content = '您已经有' + nums + '张有效优惠券咯，赶紧去花吧！';
                $(".tips").empty().append(tips_content);//后添加
            }
        } else {
            //$(".tips").empty().append("亲，暂无优惠券派发哦，敬请期待吧~");
        }
    });

    $(".btn-submit").click(function () {
        var coupon_no = $("#get_youhuiquan").val();
        console.log(coupon_no);
        //去后台判断优惠券是否有效（传 cupon_no 到后台）
        var data = {"coupon_no": coupon_no};
        var url = GLConfig.baseApiUrl + GLConfig.pull_user_coupon;

        //防止重复提交
        var bt_commit = $('.btn-submit');
        if (bt_commit.hasClass('loading')) {
            return;
        }
        bt_commit.addClass('loading');

        function callback(res) {
            bt_commit.removeClass('loading');
            if (res == "ok") {
                //有效则跳转到我的优惠券 ../pages/youhuiquan.html
                location.href = '../pages/youhuiquan.html';
            }
            else if (res == "user_not_found") {
                //无效显示无效提示（不跳转）
                var warring1 = "用户不存在~";
                $(".error-tips").append(warring1);////先清理后添加
            }
            else if (res == "not_found") {
                var warring5 = "没有找到优惠券~";
                $(".error-tips").empty().append(warring5);////先清理后添加
            }
            else if (res == "used") {
                var warring2 = "您输入的优惠券号码有误或被领取了~";
                $(".error-tips").empty().append(warring2);////先清理后添加
            }
            else if (res == "no_is_null") {
                var warring3 = "您输入的是空的~";
                $(".error-tips").empty().append(warring3);////先清理后添加
            }
            else if (res == "not_release") {
                var warring4 = "未发放优惠券~";
                $(".error-tips").empty().append(warring4);////先清理后添加
            }
            else if (res == "save error") {
                var warring6 = "保存失败~";
                $(".error-tips").empty().append(warring6);////先清理后添加
            }
        }

        $.ajax({"url": url, "data": data, "success": callback, "csrfmiddlewaretoken": csrftoken});

    });

});


function couponget_150_10() {
    //领取优惠券
    console.log("150-10");
    var url = GLConfig.baseApiUrl + GLConfig.usercoupons;
    var data = {"coupon_type": "C150_10"};
    if($(".youxiao").hasClass('loading')){
        return
    }
    $(".youxiao").addClass("loading");
    $.ajax({
        "url": url,
        "data": data,
        "success": callback,
        "type": "post",
        "csrfmiddlewaretoken": csrftoken
    });
    function callback(res) {
        $(".youxiao").removeClass("loading");
        console.log("debug 150 c :", res);
        if (res.res == "success") {
            drawToast("领取成功，赶紧去使用吧，不要过期哦！");
            //等待3秒跳转到优惠券页面
            setTimeout(function(){window.location = "youhuiquan.html";}, 3000);
        }
        if (res.res == "already") {
            drawToast("您已经领取过该优惠券啦！");
            setTimeout(function(){window.location = "youhuiquan.html";}, 3000);
        }
        if (res.res == "no_type") {
            drawToast("优惠券类型不正确呢！");
            setTimeout(function(){window.location = "youhuiquan.html";}, 3000);
        }
        if (res.res == "not_release") {
            drawToast("还没有开放该优惠券哦，敬请期待！");
            setTimeout(function(){window.location = "youhuiquan.html";}, 3000);
        }
        if (res.res == "cu_not_fund") {
            drawToast("用户未找到！尝试重新登陆");
            setTimeout(function(){window.location = "gerenzhongxin.html";}, 3000);
        }
    }
}











