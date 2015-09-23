/**
 * Created by jishu_linjie on 8/20/15.
 */

function Create_tuihuo_dom(obj) {
    var html = $("#tuihuo_list").html();
    return hereDoc(html).template(obj)
}

function create_thk_dom() {
    var html = $("#tuihuo_kong").html();
    return hereDoc(html)
}

$(document).ready(function () {
    Set_order_detail();
});

function Set_order_detail() {
    //请求URL 获取用户的所有订单
    var requestUrl = GLConfig.baseApiUrl + GLConfig.get_trade_all_url;
    //请求成功回调函数
    var requestCallBack = function (data) {
        $.each(data.results, function (index, da) {
                $.ajax({
                    type: 'get',
                    url: da.orders,
                    data: {},
                    dataType: 'json',
                    success: callBackOrder
                });
                function callBackOrder(res) {
                    for (var i = 0; i < res.count; i++) {
                        res.results[i].create = da.pay_time;
                        res.results[i].t_id = da.id;
                        if (res.results[i].refund_status != 0) {
                            res.results[i].tid = da.tid;
                            console.log("debug tid:",res.results[i]);
                            var detail_dom = Create_tuihuo_dom(res.results[i]);
                            $('.jifen-list').append(detail_dom);
                        }
                    }
                }
            }
        );
    };
    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {},
        dataType: 'json',
        success: requestCallBack
    });
}
