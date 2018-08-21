/*
 * author=kaineng.fang
 * time:2015-7-30
 * 用于取到用户的所有收获地址
 * 
 * */
$(document).ready(function () {
    init();
});
function Create_address_dom(is_default, obj) {
    var html = "";
    if (is_default) {
        html = $("#default_address").html();//默认地址显示
    }
    else {
        html = $("#usually_address").html();//普通地址显示
    }
    return hereDoc(html).template(obj);
}

function init() {
    //请求成功回调函数
    var requestUrl = GLConfig.baseApiUrl + GLConfig.get_all_address;
    var requestCallBack = function (data) {
        for (var i = 0; i < data.length; i++) {
            var address_dom = Create_address_dom(data[i].default, data[i]);
            $(".list").append(address_dom);
        }
        //删除地址
        $(" .close").each(function () {
            $(this).click(function () {
                var delete_id = $(this).parent().attr('id');
                var obj = $(this).parent();
                delete_address(obj, delete_id);
            });
        });
        //修改地址
        $(".icon-edit").each(function () {
            $(this).click(function () {
                var up_id = $(this).parent().attr('id');
                window.location.href = "shouhuodz-edit.html?id=" + up_id;
            });
        });
        $("ul li  i").each(function () {
            $(this).click(function () {
                $("ul li  i").removeClass("radio-select");//去掉之前选中的
                $(this).addClass("radio-select");//选中
                $(this).parent().css({"color": "orange", "border": "2px solid orange"});  //增加框
                $(this).parent().siblings().css({"color": "", "border": ""});  //取消框
                var default_id = $(this).parent().attr('id');
                var obj = $(this).parent();
                change_default(obj, default_id);
            });
        });
        $("ul li p").click(function () {
            $(this).parent().children("i")[0].click();
        });
    };

    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {"csrfmiddlewaretoken": csrftoken},
        dataType: 'json',
        success: requestCallBack
    });
}

function delete_address(obj, id) {
    //请求成功回调函数
    var requestUrl = GLConfig.baseApiUrl + "/address/" + id + "/delete_address";
    var requestCallBack = function (data) {
        if (data.ret == true) {
            //alert("删除地址成功");
            drawToast("删除地址成功");
            obj.remove();   //删除地址
        }
        else {
            //alert("删除失败")
            drawToast("删除地址失败");
        }
    };
    // 发送请求
    $.ajax({
        type: 'post',
        url: requestUrl,
        data: {"csrfmiddlewaretoken": csrftoken},
        dataType: 'json',
        success: requestCallBack
    });
}

function change_default(obj, id) {
    //删除地址
    //请求成功回调函数
    var requestUrl = GLConfig.baseApiUrl + "/address/" + id + "/change_default";
    var requestCallBack = function (data) {
        if (data.ret == true) {
            //判断是否是从购买页面来的如果是的则跳回去
            var source = document.referrer.split("/");
            var from_page = source[source.length-1];
            var referrer = document.referrer.split(".html")[0].split("/");
            var page = referrer[referrer.length-1];
            if(page=="buynow-dd"||page=="queren-dd"){
               window.location = from_page;
            }
            drawToast("设置默认地址成功");
        }
        else {
            drawToast("设置默认地址失败");
        }
    };
    // 发送请求
    $.ajax({
        type: 'post',
        url: requestUrl,
        data: {"csrfmiddlewaretoken": csrftoken},
        dataType: 'json',
        success: requestCallBack
    });
}



