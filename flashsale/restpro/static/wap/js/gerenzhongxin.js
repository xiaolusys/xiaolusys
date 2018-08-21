
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
    	setCookie(PROFILE_COOKIE_NAME,JSON.stringify(obj),1);
    	if (!isNone(obj.xiaolumm) && !isNone(obj.xiaolumm.id)){
			$('.userinfo-list').append(
				'<li><i class="icon icon-qiehuanzhanghao"></i>'+
				'<a href="http://m.xiaolumeimei.com/m/m/">小鹿妈妈入口</a>'.template(obj.xiaolumm)+
				'<i class="icon-jiantouyou"></i></li>')
    	}
    	var name = obj.nick!=''?obj.nick:(obj.mobile!=""?obj.mobile:'[无名]');
    	$('.userinfo .nickname span').html(name);
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
            if (data.status == 403) {
            	delCookie(PROFILE_COOKIE_NAME);
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
        delCookie(PROFILE_COOKIE_NAME);
        if (res && res.result == "logout") {
            window.location = "denglu.html";
        }
        delCookie(PROFILE_COOKIE_NAME);
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
            delCookie(PROFILE_COOKIE_NAME);
            if (data.status == 403) {
                window.location = "denglu.html";
            }
            delCookie(PROFILE_COOKIE_NAME);
        }
    });
    delCookie(PROFILE_COOKIE_NAME);
    console.log('debug cookie:',getCookie(PROFILE_COOKIE_NAME));
}

function show_grumble(location_item, text) {
    var interval;
    location_item.grumble({
        text: text,
        angle: 100,
        onShow: function () {
            var angle = 130, dir = 1;
            interval = setInterval(function () {
                (angle > 180 ? (dir = -1, angle--) : ( angle < 130 ? (dir = 1, angle++) : angle += dir));
                location_item.grumble('adjust', {angle: angle});
            }, 25);
        },
        type: 'alt-',
        hideAfter: 10000
    });
}

function need_set_info(){
	//获取设置帐号的信息
	var requestUrl = GLConfig.baseApiUrl + "/users/need_set_info";
    var pass_word =  $(".text-mimaxiugai");
    var grumble_text =  $(".text-tuihuanhuo");
	var requestCallBack = function(res){
        var result = res.result;
        if(result=="yes" || result == "1"){
            if(result=="yes"){
                pass_word.html("绑定手机");
                show_grumble(grumble_text,"您还未绑定手机哦");
            }else if(result=="1"){
                pass_word.html("设置密码");
                show_grumble(grumble_text,"您还未设置密码哦");
            }
            $(".grumble-text").click(function(){
                    window.location = "bangding.html";
                });
            //$('<div class="text">NEW</div>').insertAfter(".icon-mimaxiugai");
        }
	};
	// 请求推荐数据
	$.ajax({
		type:'get',
		url:requestUrl,
		data:{},
		dataType:'json',
		success:requestCallBack
	});

}