/**
 * Created by linjie on 15-7-18.
 */


$(".select_reason").live("change", function (e) {
    console.log('is running');
    var target = e.target;
    var id = target.getAttribute("id");
    var cid = target.getAttribute("cid");
    if (target.value !== '') {
        $(this).css("border-color", "green");
        data = {"pro_id": cid, "reason": target.value};
        url = '/refunds/refund_reason/';
        function callback(res) {
            if (res == 'ok') {
                console.log(res);
                $(target).after("<img src='/static/admin/img/icon-yes.gif'>");
            }
        }
        $.ajax({url: url, data: data, success: callback});
    }
    else {
        $(this).css("border-color", "red");
    }
});
