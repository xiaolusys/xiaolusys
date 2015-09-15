$(function () {
    $('#submit_change').bind("click", submit_data);
    $('#begin_change').bind("click", change_data);
    $('#searchbutton').bind("click", search_data);
})
function submit_data() {
    var product = $("#product").val();
    var change_data = $(".change-area");
    var result_data = {product:product}
    for (var i = 0; i < change_data.length; i++) {
        var key = change_data.eq(i).attr("id");
        result_data[key] = change_data.eq(i).val();
    }
    var requestUrl = "/items/get_sku/";
    //请求成功回调函数
    var requestCallBack = function (data) {
        console.log("ffff", data);
    };

    // 发送请求
    $.ajax({
        type: 'post',
        url: requestUrl,
        data: result_data,
        dataType: 'json',
        success: requestCallBack,
        error: function (data) {
            //if (data.status == 403) {
            //    swal({
            //        title: "Tips",
            //        text: "请先登录一下(^_^)",
            //        type: "warning",
            //        showCancelButton: false,
            //        confirmButtonText: "确定"
            //    }, function () {
            //        window.location = "/admin";
            //    });
            //} else {
            //    swal("Tips", "有错误，请联系技术人员(^_^)", "warning")
            //}
        }
    });
}
function change_data() {
    $(".change-area").attr("disabled", false);
}
function search_data() {
    $("form").submit();
}