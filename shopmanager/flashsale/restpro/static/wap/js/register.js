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
});


function my_submit() {
    var mobile = $("#mobile_username").val();
    var password1 = $("#password1").val();
    var password2 = $("#password2").val();
    if (!execReg(regCheck(4), mobile)) {
        var phone_error = $("#phone_error");
        phone_error.show();
        setTimeout("error_hide()", 2000);
    } else if ((password1 != password2) || !execReg(regCheck(2), password1) || !execReg(regCheck(2), password2)) {
        var password_error = $("#password_error");
        password_error.show();
        setTimeout("error_hide()", 2000);
    } else {
        $("#my_form").submit();

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
                    phone_exist_error.show();
                    setTimeout("error_hide()", 1000);
                }else if(result=="OK"){
                    phone_exist_error.text("可以注册").show();
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