
function province_list() {
    var selectid = document.getElementById("s_province");
    selectid.options.length = 0;
    //selectid[0] = new Option("请选择省", 0);




    //请求成功回调函数
    var requestUrl = GLConfig.baseApiUrl + GLConfig.province_list
    var requestCallBack = function (data) {

        for (var i = 1; i <= data.length; i++) {
            selectid[i] = new Option(data[i - 1].name, data[i - 1].id);
        }
        var up_id = {'up_id':getUrlParam('id')};
        xugaifuzi(up_id.up_id);
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

function province(){

 var selectid_province = document.getElementById("s_province");
  
    selectid_province[0] = new Option("请选择省", 0);
 var selectid_city = document.getElementById("s_city");
    selectid_city.options.length = 0;
    selectid_city[0] = new Option("请选择市", 0);
  var selectid_country = document.getElementById("s_country");
    selectid_country.options.length = 0;
    selectid_country[0] = new Option('请选择区/县', 0);

}


function city(){
selected_province = $("#s_province option:selected");
    province_id = selected_province.val()    //获取省份的id

if (province_id==0){
 var selectid_province = document.getElementById("s_province");
    selectid_province[0] = new Option("请选择省", 0);
 var selectid_city = document.getElementById("s_city");
    selectid_city.options.length = 0;
    selectid_city[0] = new Option("请选择市", 0);
  var selectid_country = document.getElementById("s_country");
    selectid_country.options.length = 0;
    selectid_country[0] = new Option('请选择区/县', 0);
}

else{


}

}



//第一个框的点击事件
function setSecond() {
    selected_province = $("#s_province option:selected");
    province_id = selected_province.val()    //获取省份的id
    var selectid = document.getElementById("s_city");
    selectid.options.length = 0;
    selectid[0] = new Option("请选择市", 0);
    //请求成功回调函数
    var requestUrl = GLConfig.baseApiUrl + GLConfig.city_list
    var requestCallBack = function (ret) {
		if(ret.result==true){
			var data=ret.data;
        for (var i = 1; i <= data.length; i++) {
            selectid[i] = new Option(data[i - 1].name, data[i - 1].id);

        }
       // $("#s_city option:contains(" + receiver_city + ")").attr("selected", true);
        //setThird();
	}
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
function setThird() {
    selected_city = $("#s_city option:selected");
    city_id = selected_city.val()    //获取城市的id
    var selectid = document.getElementById("s_country");
    selectid.options.length = 0;
    selectid[0] = new Option('请选择区/县', 0);
    //请求成功回调函数
    var requestUrl = GLConfig.baseApiUrl + GLConfig.country_list
    var requestCallBack = function (ret) {
//alert(data);
          console.log(ret);

if(ret.result==true){
	var data=ret.data
        for (var i = 1; i <= data.length; i++) {

            selectid[i] = new Option(data[i - 1].name, data[i - 1].id);

        }
	}
	else{
		
	}
       // $("#s_country option:contains(" + receiver_district + ")").attr("selected", true);
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

function xugaifuzi(up_id) {

    //请求成功回调函数
    var requestUrl = GLConfig.baseApiUrl + "/address/get_one_address";
    var requestCallBack = function (data) {
        console.info(data[0]);
        receiver_state = data[0].receiver_state;
        receiver_district = data[0].receiver_district;
        receiver_city = data[0].receiver_city;
        //alert(receiver_state);
       // document.getElementById("s_province")
        var selectid1 = document.getElementById("s_province");
        //$("#s_province option[text="+receiver_state+"]").attr("selected", true);
selectid1[0] = new Option(receiver_state, 0);

        var selectid2 = document.getElementById("s_city");
selectid2[0] = new Option(receiver_city, 0);

        var selectid3= document.getElementById("s_country");
selectid3[0] = new Option(receiver_district, 0);

      //  $("#s_province ").val(72);
        //setSecond();
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
    var reqUrl = GLConfig.baseApiUrl + "/address/" + id + "/update";
    var requestCallBack = function (data) {
      console.log(data);
        if(data.ret==true){
          //drawToast("收货地址修改成功");
alert("地址修改成功");
        var referrer = document.referrer;
        var hashes = referrer.split("?")[0].split('/');
        if (hashes && (hashes[hashes.length - 1] == "buynow-dd.html" || hashes[hashes.length - 1] == "queren-dd.html")) {
            window.location.href = referrer;
     
        } else {
              // drawToast("收货地址修改成功");
            window.location.href = "shouhuodz.html"
          
        }

}
else{
drawToast("收货地址修改失败");

}
        
         
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


