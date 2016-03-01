//setCookie('is_download_show', '1');


function Judge_download() {
    var is_download_show = getCookie('is_download_show');
    console.log('is_download_show: ', is_download_show);
    if (is_download_show == null) {// 如果没有cookie设置
        setCookie('is_download_show', '1', 1);
    }
    else if (is_download_show == '1') {//如果是1则显示下载按钮
        $('.sywsQwyd').show();
    }
    else {//不显示下载按钮
        $('.sywsQwyd').hide();
    }
}


$("#not_show_btn").click(function () {// 如果点击不显示
    setCookie('is_download_show', '0', 1);
    var is_download_show = getCookie('is_download_show');
    console.log("is_download_show: ", is_download_show);
    $('.sywsQwyd').hide();// 隐藏
});

$("#download_app").click(function () {//如果点击下载
    // 点击下载APP
    var requestUrl = GLConfig.baseApiUrl + GLConfig.app_download;
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {},
        dataType: 'json',
        success: requestCallBack
    });
    function requestCallBack(res){
        console.log("debug download link:",res);
        //res.download_link
        window.location = res.download_link;
    }
});