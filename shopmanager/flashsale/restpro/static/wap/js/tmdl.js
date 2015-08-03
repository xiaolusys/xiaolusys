/**
 * Created by linjie on 15-7-30.
 */


$(document).ready(function () {
    //清空输入框的内容
    $(".username").click(function () {
        $(".username_in").attr("value", "");
    });
    $(".password").click(function () {
        $(".password_in").attr("value", "");
    });

    //获取 输入框内容
    $(".btn-login").click(function () {
        var username = $(".username_in").val();
        var password = $(".password_in").val();
        var error_tips = $(".error-tips");
        var data = {"username": username, "password": password};
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
            else {
                //跳转到首页
                window.location = "../index.html";
            }
        }

        $.ajax({
            url: url, data: data, type: 'post',
            success: requestCallBack,
            error: function (data) {
                console.info("error: " + data.statusText);
            }
        })
    });
});

function error_hide() {
    $(".error-tips").hide();
}