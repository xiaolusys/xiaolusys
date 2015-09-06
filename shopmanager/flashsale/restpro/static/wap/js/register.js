/**
 * Created by yann on 15-7-21.
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
    $("#get_code_btn").click(get_code);
});


function my_submit() {
    /*
     * 表单提交
     * auther:yann
     * date:2015/30/7
     */
    var mobile = $("#mobile_username").val();
    var valid_code = $("#valid_code").val().trim();
    var password1 = $("#password1").val();
    var password2 = $("#password2").val();
    var phone_exist_error = $("#phone_exist_error");
    //请求URL
    var requestUrl = "/rest/v1/register/check_code_user";

    //请求成功回调函数
    var requestCallBack = function (res) {
        var result = res.result;
        if (result == "7") {
            drawToast("注册成功～<br>3秒后跳转到登录页面");
            setTimeout(function () {
                window.location = "denglu2.html";
            },
            3000);
        } else if (result == "0") {
            phone_exist_error.text("此手机号码已注册，您可尝试修改密码～").show();
            setTimeout("error_hide()", 1000);
        } else if (result == "3") {
            phone_exist_error.text("请点击获取验证码～").show();
            setTimeout("error_hide()", 1000);
        } else if (result == "1") {
            phone_exist_error.text("验证码有误或者过期～").show();
            setTimeout("error_hide()", 1000);
        } else if (result == "2") {
            phone_exist_error.text("表单填写有误～").show();
            setTimeout("error_hide()", 1000);
        }
    };

    //phone num and password check
    if (!execReg(regCheck(4), mobile)) {
        var phone_error = $("#phone_error");
        phone_error.show();
        setTimeout("error_hide()", 2000);
    } else if ((password1 != password2) || !execReg(regCheck(2), password1) || !execReg(regCheck(2), password2)) {
        var password_error = $("#password_error");
        password_error.show();
        setTimeout("error_hide()", 2000);
    } else {
        // 发送请求
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
            dataType: 'json',
            success: requestCallBack
        });

    }
}

function error_hide() {
    $(".error-tips").hide();
}

function get_code() {
    /*
     * 获取验证码
     * auther:yann
     * date:2015/21/7
     */
    var mobile = $("#mobile_username").val();
    var get_code_btn = $("#get_code_btn");
    var phone_exist_error = $("#phone_exist_error");
    if (!execReg(regCheck(4), mobile)) {
        var phone_error = $("#phone_error");
        phone_error.show();
        setTimeout("error_hide()", 1000);
    } else {

        $.ajax({
            type: 'post',
            url: "/rest/v1/register",
            data: {"vmobile": mobile},
            beforeSend: function () {

            },
            success: function (data) {
                var result = data.result;
                if (result == "0") {
                    phone_exist_error.text("此手机号码已注册，您可尝试修改密码~").show();
                    setTimeout("error_hide()", 3000);
                } else if (result == "OK") {
                    time(get_code_btn);
                    phone_exist_error.text("亲,验证码已经发送到手机～").show();
                    setTimeout("error_hide()", 3000);
                } else if (result == "1") {
                    phone_exist_error.text("亲,6分钟内无需重新获取～").show();
                    setTimeout("error_hide()", 3000);
                } else if (result == "2") {
                    phone_exist_error.text("亲，今日验证码获取次数已到上限～").show();
                    setTimeout("error_hide()", 3000);
                }
            },
            error: function (data) {
                if(data.status==500){
                    if($.parseJSON(data.responseText).detail=="手机号码有误"){
                        phone_exist_error.text("手机号码有误~").show();
                        setTimeout("error_hide()", 3000);
                    }
                }
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
        reg = /1[34578][0-9]{9}/;
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


var wait = 180;
function time(btn) {
    if (wait == 0) {
        btn.click(get_code);
        btn.text("获取验证码");
        wait = 180;
    } else {
        btn.unbind("click")
        btn.text(wait + "秒后重新获取");
        wait--;
        setTimeout(function () {
                time(btn);
            },
            1000)
    }
}