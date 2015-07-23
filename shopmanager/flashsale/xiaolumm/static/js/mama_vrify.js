/**
 * Created by linjie on 15-7-9.
 */
window.onload = function () {

};

function mama_verify(id) { //通过
    var index = "bt_verify_" + id;
    var url = '/m/mama_verify_action/';

    var tuijianren_id = "tuijianren_" + id;
    var weikefu_id = "weikefu_" + id;

    var tuijianren = document.getElementById(tuijianren_id).value; //获取推荐人字段 手机号码
    var weikefu = document.getElementById(weikefu_id).value; //获取微客服字段

    var bt_verify = $('#' + index);
    if (bt_verify.hasClass('loadding')) {
        return
    }
    bt_verify.addClass('loadding');
    data = {"id": id, 'tuijianren': tuijianren, 'weikefu': weikefu};


    function callback(result) {
        bt_verify.addClass('loadding');
        if (result == "ok") {
            $("#daili_"+id).attr("disabled", "disabled");
            $("#daili_" + id).html('已通过接管');
	        $('#mymodal_'+id).modal('toggle');

        }
        else if (result == "multiple") {
            alert("手机号对应多位小鹿妈妈");
        } else if (result == "unfound") {
            alert("手机号未找到小鹿妈妈");
        } else if (result == "cross") {
            alert("小鹿妈妈不能相互推荐或自荐");
        } else if (result == "already") {
            alert("小鹿妈妈已经被接管了");
        } else {
            alert("server error");
        }
    }

    $.get(url, data, callback);
}
