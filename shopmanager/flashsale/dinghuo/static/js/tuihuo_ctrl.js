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
function supplier_admin(supplier_name, mobile, address) {
    var mes = '供应商名:' + supplier_name + "电话：" + mobile + "地址：" + address;
    layer.msg(mes);
}

function change_sum_price(id, num) {
    // 退货单的id
    console.log(id, num,'dasdfasdf');
    var prom = layer.prompt({
        title: '共' + num + '件，请输入金额　并确认修改',
        formType: 0 //prompt风格，支持0-2
    }, function (sum_amount) {
        // 修改该　订货单的总金额
        change_amount(id, sum_amount);
    });

    function change_amount(id, sum_amount) {
        $.ajax({
            "url": '/sale/dinghuo/tuihuo/change_sum_amount/',
            "data": {'id': id, 'sum_amount': sum_amount},
            "type": "get",
            dataType: 'json',
            success: changeAmountCallback,
            error: function (err) {
                if (err.responseText == 'True') {
                    layer.msg('修改成功！');
                    location.reload();
                }
            }
        });
        function changeAmountCallback(res) {
            console.log('res: ', res);
            if (res.responseText == "True") {
                layer.close(prom);
            }
            else {
                layer.alert('参数错误');
            }
        }
    }
}