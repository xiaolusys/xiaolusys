(function ($) {
	$("#loading").show();
    //获取
    get_user_profile();
    $(document).on('click','.btn-logout',function () {
        logout();
    });
})(jQuery);

function get_user_profile() {
    /*
     * 获取用户信息
     * auther:yann
     * date:2015/4/8
     */
    //请求URL
    var requestUrl = GLConfig.baseApiUrl + GLConfig.get_user_profile;

    //请求成功回调函数
    var requestCallBack = function (obj) {
    	var profile_dom = $('#profile_template').html();
    	$(document.body).html(profile_dom.template(obj));
    };
    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {},
        dataType: 'json',
        success: requestCallBack,
        error: function (data) {
            if (data.statusText == "FORBIDDEN") {
                window.location = "denglu.html";
            }
            console.info("error: " + data.statusText);
        }
    });
}

function logout() {
    /*
     * 注销
     * auther:yann
     * date:2015/5/8
     */
    //请求URL
    var requestUrl = GLConfig.baseApiUrl + GLConfig.user_logout;

    //请求成功回调函数
    var requestCallBack = function (res) {
        if (res && res.result == "logout") {
            window.location = "denglu.html";
        }
    };
    // 发送请求
    $.ajax({
        type: 'post',
        url: requestUrl,
        data: {},
        dataType: 'json',
        success: requestCallBack,
        error: function (data) {
            if (data.statusText == "FORBIDDEN") {
                window.location = "denglu.html";
            }
            console.info("error: " + data.statusText);
        }
    });
}