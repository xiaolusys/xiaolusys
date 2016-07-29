/**
 * Created by jishu_linjie on 8/7/15.
 */

function Create_tuikuan_header() {
    var html = $("#tuikuan_header").html();
    return hereDoc(html);
}

function Create_tuihuo_header() {
    var html = $("#tuihuo_header").html();
    return hereDoc(html);
}

function Create_sid_commpany() {
    var html = $("#sid_company").html();
    return hereDoc(html);
}

function Create_order_top_dom(obj) {
    var html = $('#top_template').html();
    return hereDoc(html).template(obj);
}

function Create_detail_dom(obj) {
    //创建订单基本信息DOM
    var html = $("#orders_details").html();
    return hereDoc(html).template(obj);
}


function Create_refun_reason(status) {
    var html = "";
    if (status == 2) {//退款
        html = $("#refund_reason").html();
    }
    if (status == 4) {// 签收后　才允许　退货
        html = $("#refund_pro_reason").html();
    }
    $(html).appendTo("#selec_resason");
}


var swal_flag = 0;
function Set_order_detail(suffix) {
    //请求URL
    var requestUrl = GLConfig.baseApiUrl + suffix;
    //请求成功回调函数
    var requestCallBack = function (data) {
        if (typeof(data.id) != 'undifined' && data.id != null) {
            $("#shenqingjine").val(data.payment + '￥');

            if (data.status == 2) { //显示申请退款标题
                var header = Create_tuikuan_header();
                $('body').before(header);  //在body 的最前面添加
                Create_refun_reason(data.status);//创建退款原因选择
            }
            else if (data.status == 4) {//显示申请退货标题 确认签收后显示退货
                var header = Create_tuihuo_header();
                $('body').before(header);  //在body 的最前面添加
                Create_refun_reason(data.status);//创建退货原因选择
                // 这里绑定下 选择 质量问题的时候 弹出 详细
                $("#selec_resason").change(function () {
                    if ($("#selec_resason option:selected").val() == '3') {
                        setTimeout(function () {
                            $(".claps").fadeIn("slow");
                        }, "500");
                    }
                    else {
                        setTimeout(function () {
                            $(".claps").fadeOut("slow");
                        }, "500");
                    }
                });
            }
            //设置订单基本信息
            var top_dom = Create_order_top_dom(data);
            $('.basic .panel-top').append(top_dom);
            //设置订单商品明细
            var detail_dom = Create_detail_dom(data);
            $('.basic .panel-bottom').append(detail_dom);
            Handler_Refund_Infor(data.item_id, data.status);
        }
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


function getApplyFee(num) {
    // 修改退货数量　获取服务器　计算的退款金额
    var oid = $(".order_detail_num").attr('id').split("_")[2];
    var url = GLConfig.baseApiUrl + GLConfig.refunds;
    var data = {"id": oid, "num": num, 'modify': 3};
    $.ajax({
        "url": url,
        "data": data,
        "type": "post",
        dataType: 'json',
        success: getApplyFeeCallBack,
        error: function (err) {
            var resp = JSON.parse(err.responseText);
            if (!isNone(resp.detail)) {
                drawToast(resp.detail);
            }
        }
    });
    function getApplyFeeCallBack(res) {
        $("#shenqingjine").val(res.apply_fee + "￥");
    }
}

function Button_reduct_num(id) {
    var num = parseInt($("#show_num_" + id).html());
    num = num - 1;
    if (num <= 0) {
        var num = 1;
        $("#show_num_" + id).html(num);
    } else {
        $("#show_num_" + id).html(num);
    }
    getApplyFee(num);
}
function Button_plus_num(id) {
    var num = parseInt($("#show_num_" + id).html());
    var cid = parseInt($("#show_num_" + id).attr('cid'));
    num = num + 1;
    if (num > cid) {
        var num = cid;
        $("#show_num_" + id).html(num);
    } else {
        $("#show_num_" + id).html(num);
    }
    getApplyFee(num);
}


function Button_tijiao() {
    var data = {};
    var refund_reason = $("#selec_resason").val();
    //var proof_pic = "http://ww.baidu.com,http://ww.google.com,http://ww.youku.com";
    if (refund_reason == '') {
        refund_reason = 0;
    }
    var description = $("#description").val();
    var shenqingjine = $("#shenqingjine").val();

    var modify = getUrlParam('modify');  // 是否是修改内容
    if (modify) {
        modify = 1;// 不是修改页面来的
    }
    else {
        modify = 0;
    }
    if (description == '') {
        drawToast("您申请建议为空,更好的有助于售后更好的服务哦~");
    }
    else {
        var mess = "退款金额为：" + shenqingjine + "\n您确定退单？";
        var num = $(".order_detail_num").html();
        var oid = $(".order_detail_num").attr('id').split("_")[2];
        data = {
            'csrfmiddlewaretoken': csrftoken,
            "reason": refund_reason,
            "id": oid,
            "num": num,
            "description": description,
            "modify": modify
            //,'proof_pic': proof_pic
        };
        var url = GLConfig.baseApiUrl + GLConfig.refunds;
        function refundcallback() {
            window.location.href = "../pages/wodetuihuo.html";
        };
        if (swal_flag == 1) {
            swal({
                    title: "",
                    text: "已经提交过了哦~ 去首页逛逛?",
                    type: "",
                    showCancelButton: true,
                    imageUrl: "http://img.xiaolumeimei.com/logo.png",
                    confirmButtonColor: '#DD6B55',
                    confirmButtonText: "确定",
                    cancelButtonText: "取消"
                },
                function () {
                    //这里可以跳转到首页
                    location.href = "../index.html"
                }
            )
        }
        else {
            swal({
                    title: "",
                    text: mess,
                    type: "",
                    showCancelButton: true,
                    imageUrl: "http://img.xiaolumeimei.com/logo.png",
                    confirmButtonColor: '#DD6B55',
                    confirmButtonText: "确定",
                    cancelButtonText: "取消"
                },
                function () {
                    ajax_to_server();
                }
            );
        }
        function ajax_to_server() {
            $.ajax({
                "url": url,
                "data": data,
                "type": "post",
                dataType: 'json',
                success: refundcallback,
                error: function (err) {
                    var resp = JSON.parse(err.responseText);
                    if (!isNone(resp.detail)) {
                        drawToast(resp.detail);
                    }
                }
            });
        }
    }
}

function Handler_Refund_Infor(item_id, status) {// data 是订单信息
    var requestUrl = GLConfig.baseApiUrl + "/products/" + item_id;
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {},
        dataType: 'json',
        success: requestCallBack
    });
    function requestCallBack(res) {
        if (res.is_saleopen == false) {//商品已经下架了
            // 显示提示信息
            var html = "";
            if (status == 2) {
                html = '<span class="alert alert-danger"  >亲，此商品已特卖结束，仓储部门可能已整理好您购买的商品，装箱发货．' +
                '您的请求需要等待客服向仓储部门确认，祝您购物愉快!</span>';
            }
            $(".panel-top").after(html);
        }
    }
}


