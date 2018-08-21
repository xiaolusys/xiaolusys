$(function () {
    $('#submit_change').bind("click", submit_data);
    $('#begin_change').bind("click", change_data);
    $('#searchbutton').bind("click", search_data);
    $('#preview_button').bind("click", preview_view);
})
var searchtext = $("#searchtext").val();
function preview_view(){
    var url = '/items/preview_sku/?search_input=' + searchtext;
    layer.open({
        type: 2,
        title: '预览界面',
        shadeClose: true,
        shade: 0.8,
        maxmin: true,
        area: ['1000px', '600px'],
        content: url
    });
}
function submit_data() {
    var product = $("#product").val();
    var change_data = $(".change-area");
    var result_data = {product:product};
    for (var i = 0; i < change_data.length; i++) {
        var key = change_data.eq(i).attr("id");
        result_data[key] = change_data.eq(i).val();
    }
    var requestUrl = "/items/get_sku/";
    //请求成功回调函数
    var requestCallBack = function (data) {
        if(data.result == "OK"){
            swal({
                    title: "结果",
                    text: "修改成功(^_^)",
                    type: "success",
                    showCancelButton: false,
                    confirmButtonText: "预览一下"
                }, function () {
                var url = '/items/preview_sku/?search_input=' + searchtext;
                layer.open({
                    type: 2,
                    title: '预览界面',
                    shadeClose: true,
                    shade: 0.8,
                    maxmin: true,
                    area: ['1000px', '600px'],
                    content: url
                });
                });
        }else{
            swal("Tips", "有错误，请联系技术人员(^_^)", "warning")
        }
    };

    // 发送请求
    $.ajax({
        type: 'post',
        url: requestUrl,
        data: result_data,
        dataType: 'json',
        success: requestCallBack,
        error: function (data) {
            if (data.status == 403) {
                swal({
                    title: "Tips",
                    text: "请先登录一下(^_^)",
                    type: "warning",
                    showCancelButton: false,
                    confirmButtonText: "确定"
                }, function () {
                    window.location = "/admin";
                });
            } else {
                swal("Tips", "有错误，请联系技术人员(^_^)", "warning")
            }
        }
    });
}
function change_data() {
    $(".change-area").attr("disabled", false);
}
function search_data() {
    $("form").submit();
}