function Judge_download() {
    var is_download_show = getCookie('is_download_show');
    console.log('is_download_show: ', is_download_show);
    if (is_download_show == null) {// 如果没有cookie设置
        setCookie('is_download_show', '1', 1);
    }
    else if (is_download_show == '1') {//如果是1则显示下载按钮
        $('.download-banner-div').removeClass('download_hidden');
    }
    else {//不显示下载按钮
        $('.download-banner-div').addClass('download_hidden');

    }
}

function isWeiXin() {//判断当前浏览器是否是微信内置浏览器
    var ua = window.navigator.userAgent.toLowerCase();
    if (ua.match(/MicroMessenger/i) == 'micromessenger') {
        return true;
    } else {
        return false;
    }
}

$("#not_show_btn").click(function () {// 如果点击不显示
    setCookie('is_download_show', '0', 1);
    var is_download_show = getCookie('is_download_show');
    console.log("is_download_show: ", is_download_show);
    $('.download-banner-div').addClass('download_hidden');// 隐藏
});

$("#download_app").click(function () {//如果点击下载
    // 点击下载APP
    var requestUrl = GLConfig.baseApiUrl + GLConfig.app_download;
    var mm_linkid = getUrlParam("mm_linkid");
    var weixin = isWeiXin();

    if (weixin == false) {
        /////// 浏览器用法 START
        $.ajax({
            type: 'get',
            url: requestUrl,
            data: {"mm_linkid": mm_linkid},
            dataType: 'json',
            success: loadNewPageE
        });
        var winRef = window.open("", "_blank");//打开一个新的页面

        function loadNewPageE(res) {
            winRef.location = res.download_url;
        }

        //// 浏览器用法　END
    }
    else {// 微信内部直接location
        $.ajax({
            type: 'get',
            url: requestUrl,
            data: {"mm_linkid": mm_linkid},
            dataType: 'json',
            success: loadNewPage
        });
        function loadNewPage(res) {
            window.location = res.download_url;
        }
    }

});

function Scorll_scan() {
    $(window).scroll(function () {
        //console.log("滚动条高度:", parseFloat($(window).scrollTop()));
        var scroll_hight = parseFloat($(window).scrollTop());
        var down_hidden = $('.download-banner-div').hasClass('download_hidden');
        var standar_high = 145;
        if (down_hidden) {
            standar_high = 70;
        }
        console.log('scroll_hight:', scroll_hight, standar_high);
        if (scroll_hight < standar_high) {
            $('#js-fixed-nav').removeClass('fixed-nav-fixed');
            $('#js-fixed-nav').addClass('fixed-nav-relative');
            $(".top").removeClass('top_bottom');
        }
        else if (scroll_hight >= standar_high) {
            $('#js-fixed-nav').removeClass('fixed-nav-relative');
            $('#js-fixed-nav').addClass('fixed-nav-fixed');
            $(".top").addClass('top_bottom');
        }
    });
}
