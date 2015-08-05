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
    var selectid = document.getElementById("s_city");
    selectid.options.length = 0;
    selectid[0] = new Option("请选择市", 0);
    //请求成功回调函数
    var requestUrl = GLConfig.baseApiUrl + GLConfig.city_list
    var requestCallBack = function (data) {

        for (var i = 1; i <= data.length; i++) {

            selectid[i] = new Option(data[i - 1].name, data[i - 1].id);

        }

        //alert(typeof(data))
        //console.info(data)
        $("#s_city option:contains(" + receiver_city + ")").attr("selected", true);
        setThird();
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
    var selectid = document.getElementById("s_country");
    selectid.options.length = 0;
    selectid[0] = new Option('请选择区/县', 0);
    //请求成功回调函数
    var requestUrl = GLConfig.baseApiUrl + GLConfig.country_list
    var requestCallBack = function (data) {

        for (var i = 1; i <= data.length; i++) {
            //alert(data[i].name)
            selectid[i] = new Option(data[i - 1].name, data[i - 1].id);

        }
        $("#s_country option:contains(" + receiver_district + ")").attr("selected", true);
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


var receiver_state;
var receiver_district;
var receiver_city;
//shuchihua
function test(up_id) {

    selected_city = $("#s_city option:selected");
    city_id = selected_city.val()    //获取城市的id
    //alert(selected_province.val());
    //console.info(obj)
    var selectid = document.getElementById("s_country");
    selectid.options.length = 0;
    selectid[0] = new Option('请选择区/县', 0);
    //请求成功回调函数
    var requestUrl = GLConfig.baseApiUrl + "/address/get_one_address";
    var requestCallBack = function (data) {


        console.info(data[0]);

        receiver_state = data[0].receiver_state;
        receiver_district = data[0].receiver_district;
        receiver_city = data[0].receiver_city;
        $("#s_province option:contains(" + receiver_state + ")").attr("selected", true);
        setSecond();
        document.getElementById('inputReceiverAddress').value = data[0].receiver_address;
        document.getElementById('inputReceiverName').value = data[0].receiver_name;
        document.getElementById('inputReceiverMobile').value = data[0].receiver_mobile;
        document.getElementById('up_id').value = data[0].id;

    };
    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {"csrfmiddlewaretoken": csrftoken, "id": up_id},
        dataType: 'json',
        success: requestCallBack
    });
}


//修改事件

$("#btn-up").click(function () {

    var id = $('#up_id').val();

    var receiver_name = $('#inputReceiverName').val();
    var receiver_mobile = $('#inputReceiverMobile').val();
    var receiver_state = $('#s_province  option:selected').text();//省
    //alert(receiver_state);
    var receiver_city = $('#s_city  option:selected ').text()
    //alert(receiver_city);
    var receiver_district = $('#s_country  option:selected  ').text();//区
    //alert(receiver_district)
    var receiver_address = $('#inputReceiverAddress').val(); //街道详细地址
    //var receiver_zip      = $('#inputReceiverZipCode').val();
    //var checkboxDefault	  = $('#checkboxDefault').val();

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
    var reqUrl = GLConfig.baseApiUrl + GLConfig.update
    var requestCallBack = function (data) {
        alert("修改成功！")
        window.location.href = "shouhuodz.html"
    };
    // 发送请求
    $.ajax({
        type: 'post',
        url: reqUrl,
        data: {
            "csrfmiddlewaretoken": csrftoken,
            "id": id,
            "receiver_state": receiver_state,
            "receiver_city": receiver_city,
            "receiver_district": receiver_district,
            "receiver_address": receiver_address,
            "receiver_name": receiver_name,
            "receiver_mobile": receiver_mobile
        },
        dataType: 'json',
        success: requestCallBack
    });
});


