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
    post_data_to_server("ok", dom, id);
}
function verify_no(dom) {
    var dom = $(dom);
    console.log("no running");
    var id = $(dom).attr('cid');
    console.log(id, "id");
    post_data_to_server("no", dom, id);
}

function already_send(dom) {
    var dom = $(dom);
    console.log("already send running");
    var id = $(dom).attr('cid');
    console.log(id, "id");
    post_data_to_server("send", dom, id);
}


function send_ok(dom) {
    var dom = $(dom);
    console.log("already send running");
    var id = $(dom).attr('cid');
    console.log(id, "id");
    post_data_to_server("send_ok", dom, id);
}
function send_fail(dom) {
    var dom = $(dom);
    console.log("already send running");
    var id = $(dom).attr('cid');
    console.log(id, "id");
    post_data_to_server("send_fail", dom, id);
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