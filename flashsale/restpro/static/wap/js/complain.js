/**
 * Created by timi06 on 15-7-28.
 */
// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');
function my_submit() {

    var content = $('#com_content').val();
    var min = 5; //最少5个字符

    //请求URL
    var requestUrl = "/rest/v1/complain";
    //请求成功回调函数
    var requestCallBack = function (res) {
        if (res.res == true) {
            var text = "谢谢您的反馈，我们将不断完善，给您最好的服务！";
            swal({
                    title: "",
                    text: text,
                    type: "",
                    showCancelButton: true,
                    imageUrl: "http://img.xiaolumeimei.com/logo.png",
                    confirmButtonColor: '#DD6B55',
                    confirmButtonText: "确定",
                    cancelButtonText: "取消"
                },
                function () {
                    window.location = "gerenzhongxin.html";
                }
            );
        }
    };

    if (content.length < min) {
        drawToast('最少填写 ' + min + ' 个字符')
    } else {
        // 发送请求
        $.ajax({
            type: 'post',
            url: requestUrl,
            data: {
                "com_content": content,
                "csrfmiddlewaretoken": csrftoken
            },
            success: requestCallBack,
            error: function (err) {
                var resp = JSON.parse(err.responseText);
                if (!isNone(resp.detail)) {
                    drawToast(resp.detail);
                }
            }
        });
    }
}
