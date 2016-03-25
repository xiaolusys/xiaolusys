/**
 * Created by jishu_linjie on 3/22/16.
 */

$(document).ready(function () {
    $("#id_mobile_input").click(function () {// 点击输入手机号码框： 页面上调避免输入法挡住输入框
        console.log("点击输入手机号码框");
        $("body").css("margin-bottom", "200px");
        $("body").scrollTop($("body")[0].scrollHeight);
    });
});

function validateMobile(s) {
    var validateReg = /^((\+?86)|(\(\+86\)))?1\d{10}$/;
    return validateReg.test(s);
}

function validateVerifyCode(s) {
    var validateReg = /^\d{6}$/;
    return validateReg.test(s);
}

var global_timer;
function updateTime() {
    var btn = $("#id_requestcode_button");
    time_left = parseInt(btn[0].innerHTML) - 1;
    if (time_left <= 0) {
        btn.attr("status", "0");
        window.clearInterval(global_timer);
        btn[0].innerHTML = "点击重发";
    } else {
        btn[0].innerHTML = time_left.toString();
    }
}

function requestcode() {
    var btn = $("#id_requestcode_button");
    var status = btn.attr("status");
    if (status == "1" || status == "2") {
        return
    }
    var mobile = $("#id_mobile_input").val();
    if (validateMobile(mobile) == false) {
        return
    }
    btn.attr("status", "1");
    btn.html("180");
    global_timer = window.setInterval(updateTime, 1000);

    var openid = $("#id_openid").val();
    var url = "/rest/v2/send_code"; // 获取验证码
    var data = {"mobile": mobile, "action": 'bind'};

    var callback = function (res) {
        console.log('res:', res);
        if (res.rcode != 0) {
            btn.attr("status", "0");
            window.clearInterval(global_timer);
        }
        $("#id_verify_msg")[0].innerHTML = res.msg;
        console.log("res.rcode:", res.rcode);
    };
    $.ajax({url: url, type: "post", data: data, success: callback});
}

function verifycode() {
    var sms_code = $("#id_code_input").val();
    if (sms_code.length == 6) {
        var mobile = $("#id_mobile_input").val();
        var unionid = $("#id_unionid").val();
        var url = '/rest/v2/verify_code';
        var data = {"mobile": mobile, "verify_code": sms_code, "unionid": unionid, "action": "bind"};

        $.ajax({url: url, type: "post", data: data, success: callback});

        function callback(res) {
            console.log('res', res);
            $("#id_verify_msg")[0].innerHTML = res.msg;
            if (res.rcode == 0) {
                $("#next_step").attr("disabled", false);
            }
        }
    }
    else {
        console.log("sms_code.length: ", sms_code.length);
    }
}

function formCheck() {

    var mobile = $("#id_mobile_input").val();
    var sms_code = $("#id_code_input").val();
    var validm = validateMobile(mobile);
    var validc = validateVerifyCode(sms_code);
    if (validm == false) {
        alert('手机号错误');
        return false
    }
    else if (validc == false) {
        alert('验证码错误');
        return false
    }
    else {
        return true
    }
}