/**
 * Created by linjie on 15-7-24.
 */

$(document).ready(function () {
    var url = "/rest/v1/user/mycoupon/";
    $.get(url, function (res) {
        if (res.length > 0) {
            var nums = 0;
            $.each(res, function (i, val) {
                if (val.coupon_status == 3) {
                    nums = nums + 1;//有效可用的优惠券数量
                }
            });
            var tips_content = '您已经有' + nums + '张优惠券咯，赶紧去花吧，不要过期哦！';
            $(".tips").empty().append(tips_content);//后添加
        } else {
            $(".tips").empty().append("暂无优惠券,赶紧索取吧!~");
        }
    });

    $(".btn-submit").click(function () {
        var coupon_no = $("#get_youhuiquan").val();
        console.log(coupon_no);
        //去后台判断优惠券是否有效（传 cupon_no 到后台）
        var data = {"coupon_no": coupon_no};
        var url = "/mm/couponcheck/";

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
                var warring5 = "无效的优惠券~";
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
                var warring4 = "无效的优惠券~";
                $(".error-tips").empty().append(warring4);////先清理后添加
            }
        }

        $.ajax({"url": url, "data": data, "success": callback});

    });
});

