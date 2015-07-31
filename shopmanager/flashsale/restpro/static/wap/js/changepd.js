/**
 * Created by yann on 15-7-31.
 */

$(function () {
    var mobile = $("#mobile_username");
    var password1 = $("#password1");
    var password2 = $("#password2");
    $(".close").click(function (e) {
        var target = e.target;
        if (target.id == "mobile_close") {
            mobile.val("");
        }
        if (target.id == "password1_close") {
            password1.val("");
            password2.val("");
        }
    });
});

function error_hide() {
    $(".error-tips").hide();
}
function get_code() {
    /*
     * 获取验证码
     * auther:yann
     * date:2015/30/7
     */
    var mobile = $("#mobile_username").val();
    var phone_exist_error = $("#phone_exist_error");
    var requestUrl = "/rest/v1/register/change_pwd_code";
    var requestCallBack = function (result) {
        console.log("back");
        if (result == "1") {
            phone_exist_error.text("尚无该用户或者手机未绑定~").show();
            setTimeout("error_hide()", 1000);
        } else if (result == "0") {
            phone_exist_error.text("获取验证码成功,请查看手机~").show();
            setTimeout("error_hide()", 1000);
        } else if (result == "2") {
            phone_exist_error.text("亲,60s内验证码有效的").show();
            setTimeout("error_hide()", 1000);
        }
    };
    if (!execReg(regCheck(4), mobile)) {
        phone_exist_error.text("手机号码有误~").show();
        setTimeout("error_hide()", 1000);
    } else {
        // 发送请求
        console.log("begin");
        $.ajax({
            type: 'post',
            url: requestUrl,
            data: {"csrfmiddlewaretoken": csrftoken, "vmobile": mobile},
            success: requestCallBack,
            error: function (res) {
                console.log("error");
            }
        });
    }
}
function confirm_change() {
    /*
     * 修改密码提交
     * auther:yann
     * date:2015/30/7
     */
    var mobile = $("#mobile_username").val();
    var phone_exist_error = $("#phone_exist_error");
    var valid_code = $("#valid_code").val();
    var password1 = $("#password1").val();
    var password2 = $("#password2").val();
    console.log(password1, password2);
    var requestUrl = "/rest/v1/register/change_user_pwd";
    var requestCallBack = function (result) {
        console.log("back");
        if (result == "1") {
            phone_exist_error.text("尚无该用户或者手机未绑定~").show();
            setTimeout("error_hide()", 1000);
        } else if (result == "0") {
            window.location = "denglu.html"
        } else if (result == "2") {
            phone_exist_error.text("填写有误").show();
            setTimeout("error_hide()", 1000);
        } else if (result == "1") {
            phone_exist_error.text("尚无用户或者手机未绑定").show();
            setTimeout("error_hide()", 1000);
        } else if (result == "3") {
            phone_exist_error.text("验证码不对").show();
            setTimeout("error_hide()", 1000);
        } else if (result == "5") {
            phone_exist_error.text("请联系客服~").show();
            setTimeout("error_hide()", 1000);
        }
    };
    if (!execReg(regCheck(4), mobile)) {
        phone_exist_error.text("手机号码有误~").show();
        setTimeout("error_hide()", 1000);
    } else if ((password1 != password2) || !execReg(regCheck(2), password1) || !execReg(regCheck(2), password2)) {
        var password_error = $("#password_error");
        password_error.show();
        setTimeout("error_hide()", 2000);
    } else {
        // 发送请求
        console.log("begin");
        $.ajax({
            type: 'post',
            url: requestUrl,
            data: {
                "username": mobile,
                "valid_code": valid_code,
                "password1": password1,
                "password2": password2,
                "csrfmiddlewaretoken": csrftoken
            },
            success: requestCallBack,
            error: function (res) {
                console.log("error");
            }
        });
    }
}

function regCheck(type) {
    /*
     * 正则表达式匹配
     * auther:yann
     * date:2015/21/7
     */
    var reg = '';
    if (type == 1) {                    //用户名校验
        reg = /^[a-z0-9_\-]{2,20}$/ig
    } else if (type == 2) {            //密码校验
        reg = /^[a-z0-9_-]{6,18}$/;
    } else if (type == 3) {            //邮箱验证
        reg = /^([a-z0-9_\.-]+)@([\da-z\.-]+)\.([a-z\.]{2,6})$/;
    } else if (type == 4) {
        reg = /1[3458][0-9]{9}/;
    }
    return reg;
}

function execReg(reg, str) {
    var result = reg.exec(str);
    if (result == null) {
        return false;
    }
    return true;
}