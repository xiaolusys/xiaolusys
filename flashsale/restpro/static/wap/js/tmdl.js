/**
 * Created by linjie on 15-7-30.
 */

$(document).ready(function () {
    $('.ui-loader').remove();
    //清空输入框的内容
    $(".username").click(function () {
        $(".username_in").val("");
    });
    $(".password").click(function () {
        $(".password_in").val("");
    });
    $(document).on({
        tap: login_click,
        touchstart: btnPresse,
        touchend: btnUnpresse,
    }, '.btn-login');
});

function login_click() {
    var username = $(".username_in").val();
    var password = $(".password_in").val();
    var next = getUrlParam('next');
    var error_tips = $(".error-tips");
    var data = {"username": username, "password": password};
    if (!isNone(next)) {
        data['next'] = next
    }
    ;
    var url = "/rest/v1/register/customer_login";
    if (username.trim().length == 0) {
        error_tips.text("帐号不能为空～").show();
        setTimeout("error_hide()", 1000);
        return;
    } else if (password.trim().length == 0) {
        error_tips.text("密码不能为空～").show();
        setTimeout("error_hide()", 1000);
        return;
    }
    function requestCallBack(res) {
        if (res.result == 'null') {
            error_tips.text("请输入用户名以及密码！！！").show();
            setTimeout("error_hide()", 1000);
        }
        else if (res.result == 'p_error') {
            error_tips.text("密码错误~").show();
            setTimeout("error_hide()", 1000);
        }
        else if (res.result == 'u_error') {
            error_tips.text("用户不存在~").show();
            setTimeout("error_hide()", 1000);
        }
        else if (res.result == 's_error') {
            error_tips.text("账户异常~").show();
            setTimeout("error_hide()", 1000);
        }
        else if (res.result == 'no_pwd') {
            error_tips.text("账户未设置密码~").show();
            setTimeout("error_hide()", 1000);
        } else {
            //跳转到首页
            window.location = decodeURIComponent(res.next);
        }
    }

    $.ajax({
        url: url, data: data, type: 'post',
        success: requestCallBack,
        error: function (data) {
            if (data.status == 500) {
                error_tips.text("账户未设置密码").show();
                setTimeout("error_hide()", 1000);
            }
            console.log("error: " + data);
        }
    })
}
function error_hide() {
    $(".error-tips").hide();
}