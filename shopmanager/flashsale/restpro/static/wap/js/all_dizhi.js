/*
 * author=kaineng.fang
 * time:2015-7-30
 * 用于取到用户的所有收获地址
 * 
 * */


$(document).ready(function () {
    init();
});


function init() {
    //var requestUrl = GLConfig.baseApiUrl + suffix;
    //var requestUrl = "http://127.0.0.1:8000/rest/v1/address/add/";
    //请求成功回调函数
    var requestUrl = GLConfig.baseApiUrl + GLConfig.get_all_address;
    var requestCallBack = function (data) {
        for (var i = 0; i < data.length; i++) {
            if (data[i].default == true) {
                var address = "<li   id=" + data[i].id + "> <p class='p1'>" + data[i].receiver_name + data[i].receiver_mobile +
                    "</p><p class='p2'>" + data[i].receiver_state + "-" + data[i].receiver_city + "-" + data[i].receiver_district + "-" + data[i].receiver_address + "</p><a class='close'  ></a><a class='icon-edit'></a><i class='radio  radio-select'  ></i></li>"
            }
            else {

                var address = "<li   id=" + data[i].id + "> <p class='p1'>" + data[i].receiver_name + data[i].receiver_mobile +
                    "</p><p class='p2'>" + data[i].receiver_state + "-" + data[i].receiver_city + "-" + data[i].receiver_district + "-" + data[i].receiver_address + "</p><a class='close'  ></a><a class='icon-edit'></a><i class='radio '  ></i></li>"

            }
            $("ul").append(address)
        }

        $(" .close").each(function () {
            $(this).click(function () {
                //console.info($(this).parent().attr('id'));
                delete_id = $(this).parent().attr('id');
                obj = $(this).parent();
                //console.log("delete_id", delete_id);
                delete_address(obj, delete_id);
                //$(this).parent().remove()
                //$(this).parent().css({"color":"red","border":"2px solid red"});  //增加颜色
            });
        });

       //修改地址
        $(".icon-edit").each(function () {
            $(this).click(function () {
                up_id = $(this).parent().attr('id');
                window.location.href="shouhuodz-edit.html?id=" + up_id;
            });
        });

        $("ul li  i").each(function () {
            $(this).click(function () {
                $("ul li  i").removeClass("radio-select")//去掉之前选中的
                $(this).addClass("radio-select")//选中
                $(this).parent().css({"color": "red", "border": "2px solid red"});  //增加框
                $(this).parent().siblings().css({"color": "", "border": ""});  //取消框
                default_id = $(this).parent().attr('id');
                obj = $(this).parent();
                change_default(obj, default_id);
            });
        })

      //点击li也可以
      //点击li也可以
     $("ul li p").click(function () {

//console.log($(this).children());
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
            alert("删除地址成功");
            obj.remove();   //删除地址
        }
        else {
            alert("删除失败")
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

        }
        else {
            alert("送货修改失败")
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


