
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
    	GLConfig.user_profile = obj;
    	$('.userinfo .nickname span').html(obj.nick!=''?obj.nick:obj.mobile);
    	$('.userinfo .score span').html(obj.score);
    };
    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {},
        dataType: 'json',
        success: requestCallBack,
        error: function (data) {
        	console.log('debug profile:',data)
            if (data.status == 403) {
                drawToast('当前用户为游客身份');
            }
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
            console.log('debug profile:',data)
            if (data.status == 403) {
                window.location = "denglu.html";
            }
        }
    });
}