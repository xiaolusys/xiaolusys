/**
 * Created by linjie on 15-7-24.
 */


$(document).ready(function () {
    console.log('get youhuiquan is running');

    $(".btn-submit").click(function () {
        var coupon_no = $("#get_youhuiquan").val();
        console.log(coupon_no);
        //去后台判断优惠券是否有效（传 cupon_no 到后台）
        var data = {"coupon_no": coupon_no};
        var url = "/mm/couponcheck/";

        function callback(res) {
            if (res == "ok") {
                //有效则跳转到我的优惠券 /static/wap/pages/youhuiquan.html
                location.href = '/static/wap/pages/youhuiquan.html';
            }
            else if (res == "user_not_found") {
                console.log('user_not_found');
                //无效显示无效提示（不跳转）
                $(".error-tips").empty();//先清理
                var tishi = "用户不存在~";
                $(".error-tips").append(tishi);//后添加
            }
            else if (res == "not_found") {
                console.log('优惠券不存在');
            }
            else if (res == "used") {
                $(".error-tips").empty();//先清理
                var tishi = "您输入的优惠券号码有误或被领取了~";
                $(".error-tips").append(tishi);//后添加
            }
            else if (res == "no_is_null") {
                $(".error-tips").empty();//先清理
                var tishi = "您输入的是空的~";
                $(".error-tips").append(tishi);//后添加
            }
            else if(res=="not_release") {
                $(".error-tips").empty();//先清理
                var tishi = "无效的优惠券";
                $(".error-tips").append(tishi);//后添加
            }
        }

        $.ajax({"url": url, "data": data, "success": callback});

    });
});

