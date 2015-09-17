/**
 * Created by jishu_linjie on 9/15/15.
 */

// 售后退款页面　弹出页面　操作等js代码
function show_page(refund_id) {
    $(".click_row_"+refund_id).parent().css('color','red');//隐藏掉要操作的行
    console.log("debug refund id :", refund_id);
    layer.open({
        type: 2,
        title: '退款审核页面',
        shadeClose: true,
        shade: 0.6,
        area: ['950px', '70%'],
        content: '/mm/refund_pop_page/?pk=' + refund_id // 弹出的url页面
    });
}


function Create_btn(status) {
    function Btn_Dom1() {
        /*
         <button type="button" class="btn btn-danger btn_dnt_agree"　style="margin-left: 30px">驳回申请</button>
         <button type="button" class="btn btn-success btn_agree" style="margin-left :30px">同意退款</button>
         */
    }

    function Btn_Dom2() {
        /*
         <button type="button" class="btn btn-info btn_confirm" style="margin-left :30px">确认退款完成</button>
         */
    }

    if (status == "买家已经申请退款" || status == "卖家已经同意退款" || status == "买家已经退货") {
        return hereDoc(Btn_Dom1);
    }
    else if (status == "确认退款，等待返款") {
        return hereDoc(Btn_Dom2);
    }
}


//　保存
function save_info(refund_id) {
    console.log(refund_id);
    var requestUrl = "/mm/refund_pop_page/";
    var refund_status = $("#ref_status").val();
    var refund_feedback = $("#ref_feedback").val();
    var add_content = $("#add_content").val();
    refund_feedback = refund_feedback + add_content;  //追加审核意见内容
    console.log(refund_status, refund_feedback);
    layer.confirm("确定保存？", {btn: ["确定", '取消']},
        function () {
            $.ajax({
                type: 'post',
                url: requestUrl,
                data: {
                    "pk": refund_id,
                    "refund_status": refund_status,
                    "refund_feedback": refund_feedback,
                    "method": "save"
                },
                dataType: 'json',
                success: requestCallBack
            });
        }, function () {
            console.log("cancel save");
        }
    );
    function requestCallBack(res) {
        console.log(res);
        if (res.res == true) {
            layer.msg('操作成功！');
            var index = parent.layer.getFrameIndex(window.name); //获取当前窗体索引
            parent.layer.close(index); //执行关闭
        }
    }
}

//　驳回申请
function dnt_agree_refund(refund_id) {
    console.log(refund_id);
    var requestUrl = "/mm/refund_pop_page/";
    var refund_feedback = $("#ref_feedback").val();
    var add_content = $("#add_content").val();
    refund_feedback = refund_feedback + add_content;  //追加审核意见内容
    layer.confirm('请确定填写审核意见，要驳回申请么？', {
        btn: ['确定', '取消'] //按钮
    }, function () {
        $.ajax({//　确定驳回申请
            type: 'post',
            url: requestUrl,
            data: {"pk": refund_id, "refund_feedback": refund_feedback, "method": "reject"},
            dataType: 'json',
            success: requestCallBack
        });
    }, function () {
        console.log("cancel reject")
    });

    function requestCallBack(res) {
        console.log(res);
        if (res.res == "not_in_status") {
            layer.msg('不在驳回状态！');
        }
        else if (res.res == "sys_error") {
            layer.msg('系统出错！');
        }
        else if (res.res == true) {
            layer.msg('操作成功！');
            //关闭当前页面
            var index = parent.layer.getFrameIndex(window.name); //获取当前窗体索引
            parent.layer.close(index); //执行关闭
        }
    }
}

//　同意退款　　　状态改为　确认退款等待返款　
function agree_refund(refund_id) {
    console.log(refund_id);
    var requestUrl = "/mm/refund_pop_page/";
    var refund_feedback = $("#ref_feedback").val();
    var add_content = $("#add_content").val();
    refund_feedback = refund_feedback + add_content;  //追加审核意见内容
    layer.confirm("请确定退款金额，同意退款么？", {btn: ["确定", "取消"]},
        function () {
            if ($(".layui-layer-btn0").hasClass('loading')) {
                return
            }
            $(".layui-layer-btn0").addClass("loading");
            $.ajax({
                type: 'post',
                url: requestUrl,
                data: {"pk": refund_id, "method": "agree", "refund_feedback": refund_feedback},
                dataType: 'json',
                success: requestCallBack
            });
        }, function () {
            console.log("cancel agree")
        }
    );

    function requestCallBack(res) {
        $(".layui-layer-btn0").removeClass('loading');
        console.log(res);
        if (res.res == "not_in_status") {
            layer.msg('不在状态！');
        }
        else if (res.res == "sys_error") {
            layer.msg('系统出错！');
        }
        else if (res.res == true) {
            layer.msg('操作成功！');
            //关闭当前页面
            var index = parent.layer.getFrameIndex(window.name); //获取当前窗体索引
            parent.layer.close(index); //执行关闭
        }
    }
}

//　确认退款完成　状态为　　退款成功
function confirm_refund(refund_id) {
    //
    console.log(refund_id);
    var requestUrl = "/mm/refund_pop_page/";
    var refund_feedback = $("#ref_feedback").val();
    var add_content = $("#add_content").val();
    refund_feedback = refund_feedback + add_content;  //追加审核意见内容
    layer.confirm('确定退款成功么？', {btn: ["确定", "取消"]}, function () {
        $.ajax({
            type: 'post',
            url: requestUrl,
            data: {"pk": refund_id, "method": "confirm", "refund_feedback": refund_feedback},
            dataType: 'json',
            success: requestCallBack
        });
    }, function () {
        console.log("cancel confirm");
    });

    function requestCallBack(res) {
        console.log(res);
        if (res.res == "no_complete") {
            layer.msg('没有完成！');
        }
        else if (res.res == "sys_error") {
            layer.msg('系统出错！');
        }
        else if (res.res == true) {
            layer.msg('操作成功！');
            //关闭当前页面
            var index = parent.layer.getFrameIndex(window.name); //获取当前窗体索引
            parent.layer.close(index); //执行关闭
        }
    }
}

//定义多行字符串函数实现
function hereDoc(f) {
    return f.toString().replace(/^[^\/]+\/\*!?\s?/, '').replace(/\*\/[^\/]+$/, '');
}