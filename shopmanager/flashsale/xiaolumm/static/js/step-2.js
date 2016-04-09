/**
 * Created by jishu_linjie on 3/22/16.
 */
function isWeiXin() {//判断当前浏览器是否是微信内置浏览器
    var ua = window.navigator.userAgent.toLowerCase();
    if (ua.match(/MicroMessenger/i) == 'micromessenger') {
        return true;
    } else {
        return false;
    }
}
function clickAlipay() {
    $("#alipay-grey").click(function () {//点击灰色支付宝　显示亮色支付宝
        console.log('click grey');
        $("#alipay-grey").removeClass('active');
        $("#alipay-light").addClass('active');

        // 变灰微信支付
        $("#weichatpay-icon-light").removeClass('active');
        $("#weichatpay-icon-grey").addClass('active');

        $("#channel_value").val('alipay_wap');
    });

    $("#alipay-light").click(function () {//点击亮色支付宝　显示灰色支付宝
        console.log('click light');
        $("#alipay-light").removeClass('active');
        $("#alipay-grey").addClass('active');
        var in_weixin = isWeiXin();
        if (in_weixin) {
            $("#channel_value").val('wx_pub');
        }
    });
}

function clickWeiXinPay() {
    $("#weichatpay-icon-grey").click(function () {//点击灰色微信　显示亮色微信
        console.log('click grey');
        $("#weichatpay-icon-grey").removeClass('active');
        $("#weichatpay-icon-light").addClass('active');

        // 变灰支付宝按钮
        $("#alipay-light").removeClass('active');
        $("#alipay-grey").addClass('active');

        $("#channel_value").val('wx_pub');
    });
    $("#weichatpay-icon-light").click(function () {//点击亮色微信　显示灰色微信
        console.log('click light');
        $("#weichatpay-icon-light").removeClass('active');
        $("#weichatpay-icon-grey").addClass('active');
        $("#channel_value").val('alipay_wap');

    });
}

$(document).ready(function () {
    console.log('rungning');

    var in_weixin = isWeiXin();// 微信里面支持支付宝和微信支付两种形式
    if (in_weixin == true) {
        clickAlipay();
        clickWeiXinPay();
    }

    else {//不在微信里面
        console.log('not in weixin');
        // 删除微信图标的显示　显示灰色
        if ($("#weichatpay-icon-light").hasClass('active')) {
            $("#weichatpay-icon-light").removeClass('active');
        }
        if ($("#weichatpay-icon-grey").hasClass('active') == false) {
            $("#weichatpay-icon-grey").addClass('active');
        }
        clickAlipay()
    }

    //debug_test();
});
var debug_click_time = 0;

function debug_test() {
    $("#post-data-debug").click(function () {
        console.log(debug_click_time);
        if (debug_click_time >= 8) {
            var params = $('#deposite-form').serialize();
            alert(params);
        }
        debug_click_time += 1;
    });
}

function Submit_enable(ele) {
    if (ele.checked) {
        $('#btn-pay').removeAttr('disabled');
    } else {
        $('#btn-pay').attr('disabled', 'disabled');
    }
}
