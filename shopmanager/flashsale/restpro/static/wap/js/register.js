/**
 * Created by yann on 15-7-21.
 */


// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

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


function my_submit() {
    var mobile = $("#mobile_username").val();
    var valid_code = $("#valid_code").val();
    var password1 = $("#password1").val();
    var password2 = $("#password2").val();

    //请求URL
    var requestUrl = "/rest/v1/register/check_code_user";

    //请求成功回调函数
    var requestCallBack = function (res) {
        console.log(res);
        if (res == "7") {
            window.location = "denglu2.html";
        } else if (res == "0") {
            show_message("已经注册过");
        } else if (res == "3") {
            alert("重新获取验证码");
        } else if (res == "1") {

            show_message("验证码不对")
        } else if (res == "2") {
            show_message("表单填写有误");
        }
    };


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
    var mobile = $("#mobile_username").val();
    var phone_exist_error = $("#phone_exist_error");
    if (!execReg(regCheck(4), mobile)) {
        var phone_error = $("#phone_error");
        phone_error.show();
        setTimeout("error_hide()", 1000);
    } else {
        $.post("/rest/v1/register", {"vmobile": mobile},
            function (result) {
                console.log(result);
                if (result == "0") {
                    phone_exist_error.text("此手机号码已注册，您可尝试修改密码~").show();
                    setTimeout("error_hide()", 1000);
                } else if (result == "OK") {
                    phone_exist_error.text("可以注册").show();
                    setTimeout("error_hide()", 1000);
                }else if(result == "1"){
                    phone_exist_error.text("亲,60s内验证码有效的").show();
                    setTimeout("error_hide()", 1000);
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

/*
* 模拟toast
* */
var intervalCounter = 0;
function hideToast() {
    var alert = document.getElementById("toast");
    alert.style.opacity = 0;
    clearInterval(intervalCounter);
}
function drawToast(message) {
    var alert = document.getElementById("toast");
    if (alert == null) {
        var toastHTML = '<div id="toast">' + message + '</div>';
        document.body.insertAdjacentHTML('beforeEnd', toastHTML);
    }
    else {
        alert.style.opacity = .9;
    }
    intervalCounter = setInterval("hideToast()", 1000);
}
function show_message(message) {
    drawToast(message);
}