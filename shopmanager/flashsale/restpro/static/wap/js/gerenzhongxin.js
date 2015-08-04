(function ($) {
    //获取
    get_user_info();
    get_point();
})(jQuery);

function get_user_info() {
    /*
     * 获取用户信息
     * auther:yann
     * date:2015/4/8
     */
    //请求URL
    var requestUrl = GLConfig.baseApiUrl + GLConfig.get_user_info;

    //请求成功回调函数
    var requestCallBack = function (res) {
        if (res.results != null){
            $(".nickname").html("昵称:"+res.results[0].nick);
        }
    };
    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {},
        dataType: 'json',
        beforeSend: function () {

        },
        success: requestCallBack,
        error: function (data) {
            if (data.statusText == "FORBIDDEN") {
                window.location = "denglu2.html";
            }
            console.info("error: " + data.statusText);
        }
    });
}

function get_point() {
    /*
     * 获取用户积分
     * auther:yann
     * date:2015/4/8
     */
    //请求URL
    var requestUrl = GLConfig.baseApiUrl + GLConfig.get_user_point;

    //请求成功回调函数
    var requestCallBack = function (res) {
        console.log(res.results.length);
        if (res.results != null && res.results.length > 0){
            $(".score").html("积分:"+res.results[0].integral_value);
        }else{
            $(".score").html("积分:"+"0");
        }
    };
    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {},
        dataType: 'json',
        beforeSend: function () {

        },
        success: requestCallBack,
        error: function (data) {
            if (data.statusText == "FORBIDDEN") {
                window.location = "denglu2.html";
            }
            console.info("error: " + data.statusText);
        }
    });
}