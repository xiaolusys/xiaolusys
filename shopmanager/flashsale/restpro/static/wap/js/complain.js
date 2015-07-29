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
            // Does this cookie string begin with the name we want?
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

    var content = document.getElementById('com_content').value;
    var min = 5; //最少5个字符

    //请求URL
    var requestUrl = "/rest/v1/complain";

    //请求成功回调函数
    var requestCallBack = function (res) {
        alert("提交成功！谢谢您的反馈，我们将不断完善，给您最好的服务！")
        window.location = "gerenzhongxin.html";

    };

    if(content.length < min){
        alert('最少填写 '+min+' 个字符')
    }else{
        // 发送请求
        $.ajax({
            type: 'post',
            url: requestUrl,
            data: {
                "com_content": content,
                "csrfmiddlewaretoken": csrftoken
            },

            success: requestCallBack
        });
    }
}