/**
 * Created by jishu_linjie on 10/9/15.
 */

$(document).ready(function () {
});

function verify_ok(dom) {
    var dom = $(dom);
    console.log("ok running");
    var id = $(dom).attr('cid');
    console.log(id, "id");
    layer.confirm('您确定审核通过？　通过将减去对应商品的库存数量', {
        btn: ['确定', '取消'] //按钮
    }, function () {
        post_data_to_server("ok", dom, id);
    }, function () {
    });

}
function verify_no(dom) {
    var dom = $(dom);
    console.log("no running");
    var id = $(dom).attr('cid');
    console.log(id, "id");

    layer.confirm('您确定作废退货单？', {
        btn: ['确定', '取消'] //按钮
    }, function () {
        post_data_to_server("no", dom, id);
    }, function () {
    });
}

function already_send(dom) {
    var dom = $(dom);
    console.log("already send running");
    var id = $(dom).attr('cid');
    console.log(id, "id");
    layer.confirm('您确定已经将该退货单核实　并　发货给供应商？', {
        btn: ['确定', '取消'] //按钮
    }, function () {
        post_data_to_server("send", dom, id);
    }, function () {
    });
}


function send_ok(dom) {
    var dom = $(dom);
    console.log("already send running");
    var id = $(dom).attr('cid');
    console.log(id, "id");
    layer.confirm('您确定　供应商　已经收到退货产品了吗？', {
        btn: ['确定', '取消'] //按钮
    }, function () {
        post_data_to_server("send_ok", dom, id);
    }, function () {
    });
}
function send_fail(dom) {
    var dom = $(dom);
    console.log("already send running");
    var id = $(dom).attr('cid');
    console.log(id, "id");
    layer.confirm('退货失败了吗？', {
        btn: ['确定', '取消'] //按钮
    }, function () {
        post_data_to_server("send_fail", dom, id);
    }, function () {
    });
}


function post_data_to_server(act, dom, id) {
    if (dom.hasClass("loading")) {
        return
    }
    dom.addClass("loading");
    var url = "/sale/dinghuo/tuihuo/change_status/";
    var data = {"act_str": act, "id": id};
    $.ajax({"url": url, "data": data, "type": "post", "success": callback});
    function callback(res) {
        dom.removeClass("loading");
        console.log(res);
        if (res == "True") {
            //刷新当前页面
            window.location.reload();
        }
    }

}