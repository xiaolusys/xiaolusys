/**
 * Created by linjie on 15-7-9.
 */

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
    var data = {"id": id, 'tuijianren': tuijianren, 'weikefu': weikefu};

    $.get(url, data, callback);

    function callback(result) {
        bt_verify.addClass('loadding');
        //ajax 获取　task id 的结果
        console.log("debug result:", result);
        var requestUrl = "/djcelery/" + result + "/status";
        task_ajax(requestUrl, result);
    }

    function task_ajax(requestUrl) {
        function requestCallBack(task_res) {
            console.log("debug task_res result :", task_res.task.status);
            var task_message = task_res.task.result;
            if(task_res.task.status =="FAILURE"){
                 alert("任务失败！");
            }
            else if (task_res.task.status != "SUCCESS") {
                    task_ajax(requestUrl);
                }
            else if (task_message == "ok") {
                $("#daili_" + id).attr("disabled", "disabled");
                $("#daili_" + id).html('已通过接管');
                $('#mymodal_' + id).modal('toggle');
            }
            else if (task_message == "multiple") {
                alert("手机号对应多位小鹿妈妈");
            } else if (task_message == "unfound") {
                alert("手机号未找到小鹿妈妈");
            } else if (task_message == "cross") {
                alert("小鹿妈妈不能相互推荐或自荐");
            } else if (task_message == "already") {
                alert("小鹿妈妈已经被接管了");
            }
            else if (task_message == "l_error") {
                alert("推荐人代理级别有问题，请管理员检查下");
            }
            else if(task_message == "reject"){
                alert("钱包里面有此人的记录");
            }
            else if(task_message =="carry_multiple"){
                alert("钱包里面有此人多条记录");
            }
            else {
                alert("未知错误，联系技术人员");
            }
        }
        $.ajax({
            type: 'get',
            url: requestUrl,
            data: {},
            dataType: 'json',
            success: requestCallBack,
            error: function (data) {
                if (data.statusText == "FORBIDDEN") {
                    alert("状态异常");
                }
            }
        });
    }




}
