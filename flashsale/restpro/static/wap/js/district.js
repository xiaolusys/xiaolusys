/*
 * author :方凯能
 * 内容：增加收货地址
 * 日期：2015-8-1
 * */











//$(function(){
//alert("ok");
province_list();


//})

function province_list() {
    var selectid = document.getElementById("s_province");
    selectid.options.length = 0;
    selectid[0] = new Option("请选择省", 0);
    //selectid[0]=new Option("---- 设置显示0 ----",0);
    // selectid[1]=new Option("---- 设置显示1 ----",1);
    //selectid[2]=new Option("---- 设置显示2 ----",2);
    //请求成功回调函数
    var requestUrl = GLConfig.baseApiUrl + GLConfig.province_list
    var requestCallBack = function (data) {
        //alert(typeof(data))
        //console.info(data)
        for (var i = 1; i <= data.length; i++) {
            //alert(data[i].name)
            selectid[i] = new Option(data[i - 1].name, data[i - 1].id);
        }
        //if(data.ret==true){
        //alert("success");
        //	}
        //	else{
        //alert("删除失败")

        //	}
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


//第一个框的点击事件
function setSecond(obj) {
    selected_province = $("#s_province option:selected");
    province_id = selected_province.val()    //获取省份的id
    //alert(selected_province.val());
    //console.info(obj)
    var selectid = document.getElementById("s_city");
    selectid.options.length = 0;
    selectid[0] = new Option("请选择市", 0);
    //请求成功回调函数
    var requestUrl = GLConfig.baseApiUrl + GLConfig.city_list
    var requestCallBack = function (ret) {
if (ret.result==true){
	var data=ret.data;
        for (var i = 1; i <= data.length; i++) {
            //alert(data[i].name)
            selectid[i] = new Option(data[i - 1].name, data[i - 1].id);

        }
}
else{
	
}
        //alert(typeof(data))
        //console.info(data)

    };
    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {"csrfmiddlewaretoken": csrftoken, "id": province_id},
        dataType: 'json',
        success: requestCallBack
    });


}

//城市框的点击事件
function setThird(obj) {
    selected_city = $("#s_city option:selected");
    city_id = selected_city.val()    //获取城市的id
    //alert(selected_province.val());
    //console.info(obj)
    var selectid = document.getElementById("s_country");
    selectid.options.length = 0;
    selectid[0] = new Option('请选择区/县', 0);
    //请求成功回调函数
    var requestUrl = GLConfig.baseApiUrl + GLConfig.country_list
    var requestCallBack = function (ret) {

 if (ret.result==true){
	 var data=ret.data;
        for (var i = 1; i <= data.length; i++) {
            //alert(data[i].name)
            selectid[i] = new Option(data[i - 1].name, data[i - 1].id);
        }
	}
	else{
		
	}
        //alert(typeof(data))
        //console.info(data)
    };
    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {"csrfmiddlewaretoken": csrftoken, "id": city_id},
        dataType: 'json',
        success: requestCallBack
    });
}


//保存事件

$(".btn-save").bind("click", btn_save_func);
function btn_save_func () {
    //alert("保存");
    var receiver_name = $('#inputReceiverName').val();
    var receiver_mobile = $('#inputReceiverMobile').val();
    var receiver_state = $('#s_province  option:selected').text();//省
    var receiver_city = $('#s_city  option:selected ').text()
    var receiver_district = $('#s_country  option:selected  ').text();//区
    var receiver_address = $('#inputReceiverAddress').val(); //街道详细地址

    if (receiver_state == '请选择省' || receiver_state == '') {
        $('p').html('请选择省份');
        return false
    }
    if (receiver_city == '请选择市' || receiver_city == '') {
        $('p').html('请选择城市');
        return false
    }

    if (receiver_district == '请选择区/县' || receiver_district == '') {
        $('p').html('请选择区/县');
        return false
    }
    if (receiver_address == '') {
        $('p').html('请填写收货详细地址');
        return false
    }
    if (receiver_name == '') {
        $('p').html('请填写收货人姓名');
        return false
    }
    if (receiver_mobile == '' || !/^1[0-9]{10}$/.test(receiver_mobile)) {
        $('p').html('请填写正确的收货人手机');
        return false
    }
    //请求成功回调函数
    var requestUrl = GLConfig.baseApiUrl + GLConfig.create_address
    var requestCallBack = function (data) {
        var referrer = document.referrer;
        var hashes = referrer.split("?")[0].split('/');
        if (hashes && (hashes[hashes.length - 1] == "buynow-dd.html" || hashes[hashes.length - 1] == "queren-dd.html")) {
            window.location = referrer;
        } else {
            window.location = "shouhuodz.html"
        }
    };
    $(".btn-save").unbind("click");
    $(".btn-save").css("background-color","#898383");
    setTimeout(function () {
            $(".btn-save").bind("click", btn_save_func);
            $(".btn-save").css("background-color","#fcb916");
        },
        5000);
    // 发送请求
    $.ajax({
        type: 'post',
        url: requestUrl,
        data: {
            "csrfmiddlewaretoken": csrftoken,
            "receiver_state": receiver_state,
            "receiver_city": receiver_city,
            "receiver_district": receiver_district,
            "receiver_address": receiver_address,
            "receiver_name": receiver_name,
            "receiver_mobile": receiver_mobile,
        },
        dataType: 'json',
        success: requestCallBack
    });


}












