/**
 * Created by linjie on 15-7-31.
 */

$(document).ready(function () {
    $(".has_out_stock").live("change", function (e) {
        var target = e.target;
        var cid = target.getAttribute("cid");
        if (target.value !== '') {
            $(this).css("border-color", "green");
            data = {"tid": cid, "stock": target.value};
            url = '/trades/select_stock/';
            function callback(res) {
                if (res == 'ok') {
                    $(target).after("<img src='/static/admin/img/icon-yes.gif'>");
                }
            }

            $.ajax({url: url, data: data, success: callback,type: 'post'});
        }
        else {
            $(this).css("border-color", "red");
        }
    });
});
