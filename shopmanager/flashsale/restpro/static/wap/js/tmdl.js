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
        console.log(username, password);
        var data = {"username":username,"password":password};
        var url = "/rest/v1/register/customer_login";

        function requestCallBack(res){
            if (res=='null'){
                console.log('有空项  请输入用户名以及密码！！！');
            }
            else if(res=='p_error'){
                console.log('密码错误');
            }
            else if(res=='u_error'){
                console.log('用户名错误')
            }
            else if(res=='s_error'){
                console.log('账户异常')
            }
            else{
                console.log(res);
                //跳转到首页
                window.location = "../index.html";
            }
        }
        $.ajax({
            url: url, data: data, type: 'post',
            beforeSend: function () {
                $("#loading").show();
            },
            success: requestCallBack,
            error: function (data) {
                if (data.statusText == "FORBIDDEN") {
                    window.location = "denglu2.html";
                }
                console.info("error: " + data.statusText);
            }
        })
    });
});