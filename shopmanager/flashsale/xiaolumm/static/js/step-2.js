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

        $("#optionsRadios2").attr("checked", true);// 设置支付宝的时候关闭微信
        $("#optionsRadios1").attr("checked", false);// 关闭微信
    });

    $("#alipay-light").click(function () {//点击亮色支付宝　显示亮色支付宝
        console.log('click light');
        $("#alipay-light").removeClass('active');
        $("#alipay-grey").addClass('active');
        $("#optionsRadios2").attr("checked", false);
    });
}

function clickWeiXinPay() {
    $("#weichatpay-icon-grey").click(function () {//点击灰色支付宝　显示亮色支付宝
        console.log('click grey');
        $("#weichatpay-icon-grey").removeClass('active');
        $("#weichatpay-icon-light").addClass('active');

        // 变灰支付宝按钮
        $("#alipay-light").removeClass('active');
        $("#alipay-grey").addClass('active');


        $("#optionsRadios1").attr("checked", true);// 设置微信的时候
        $("#optionsRadios2").attr("checked", false);// 关闭支付宝
    });
    $("#weichatpay-icon-light").click(function () {//点击亮色支付宝　显示亮色支付宝
        console.log('click light');
        $("#weichatpay-icon-light").removeClass('active');
        $("#weichatpay-icon-grey").addClass('active');
        $("#optionsRadios1").attr("checked", false);

    });
}

$(document).ready(function () {
    console.log('rungning');

    var in_weixin = isWeiXin();// 微信里面支持支付宝和微信支付两种形式
    in_weixin = true;
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


});


function Submit_enable(ele) {
    if (ele.checked) {
        $('#btn-pay').removeAttr('disabled');
    } else {
        $('#btn-pay').attr('disabled', 'disabled');
    }
}

function Confirm_charge() {
    var CHARGE_URL = window.location.href;
    var params = $('#deposite-form').serialize();
    console.log('pay info:', params);
    var callBack = function (data) {
        console.log('charge resp:', data);
        var redirect_url = './';
        pingpp.createPayment(data, function (result, err) {
            alert('err:' + err);
            console.log(err);
            if (result == "success") {
                redirect_url = '{{success_url}}?out_trade_no=' + params['uuid'];
            } else if (result == "fail") {
                redirect_url = '{{cancel_url}}?mama_id={{referal_mamaid}}';
            } else if (result == "cancel") {
                redirect_url = '{{cancel_url}}?mama_id={{referal_mamaid}}';
            }
            //window.location.href = redirect_url;
        });
    };
    // 调用接口
    $.ajax({
        type: 'post',
        url: CHARGE_URL,
        data: params,
        dataType: 'json',
        success: callBack,
        error: function (err) {
            click_paybtn = false;
            console.log("err is here ", err);
            var resp = JSON.parse(err.responseText);
            if (!isNone(resp.detail)) {
                alert(resp.detail);
            } else {
                alert('支付异常!');
            }
        }
    });
};