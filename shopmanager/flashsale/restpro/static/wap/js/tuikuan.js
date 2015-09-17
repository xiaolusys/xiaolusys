/**
 * Created by jishu_linjie on 8/7/15.
 */
var refund_or_pro = 0;//0表示退款　１表示退货退款

function Create_tuikuan_header() {
    var html = $("#tuikuan_header").html();
    return hereDoc(html);
}

function Create_tuihuo_header() {
    var html = $("#tuihuo_header").html();
    refund_or_pro = 1;
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
    if (status==2){//退款
        html = $("#refund_reason").html();
    }
    if (status==3){//退货
        html = $("#refund_pro_reason").html();
    }
    $(html).appendTo("#selec_resason");
}


var swal_flag = 0;
function Set_order_detail(suffix) {

    //请求URL
    var requestUrl = GLConfig.baseApiUrl + suffix;
    console.log(requestUrl, "requestUrl requestUrl requestUrl");
    //请求成功回调函数
    var requestCallBack = function (data) {
        if (typeof(data.id) != 'undifined' && data.id != null) {
            var refun_status = (data.refund_status_display);
            console.log(refun_status, 'refun_status');
            //if (refun_status == "没有退款") {
            //    swal_flag = 1;
            //}
            //else {
            //    swal_flag = 0;
            //}
            if (data.status == 2) { //显示申请退款标题
                console.log(data.status, '订单状态');
                var header = Create_tuikuan_header();
                $('body').before(header);  //在body 的最前面添加
                Create_refun_reason(data.status);//创建退款原因选择

            }
            else if (data.status == 3) {//显示申请退货标题
                console.log(data.status, '订单状态');
                var header = Create_tuihuo_header();
                $('body').before(header);  //在body 的最前面添加
                Create_refun_reason(data.status);//创建退货原因选择
            }
            //设置订单基本信息
            var top_dom = Create_order_top_dom(data);
            $('.basic .panel-top').append(top_dom);
            //设置订单商品明细
            var detail_dom = Create_detail_dom(data);
            $('.basic .panel-bottom').append(detail_dom);
            Handler_Refund_Infor(data.item_id, data.status);


        }
        var order_payment = $("#order_payment").html().split(">")[2];
        $("#shenqingjine").keyup(function () {
            var refund_fee = parseFloat(($(this).val()).trim());
            console.log("debug refund_fee :", refund_fee);
            var checkNum = /^(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))$/;
            if (!checkNum.test(refund_fee)) {
                drawToast("您申请金额填写的不正确哦~");
            }
            if (refund_fee > order_payment) {
                drawToast("您申请金额超过了可以申请的金额哦~");
            }
        });
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

function Button_reduct_num(id) {
    var num = parseInt($("#show_num_" + id).html());
    var num = num - 1;
    if (num <= 0) {
        var num = 1;
        $("#show_num_" + id).html(num);
    } else {
        $("#show_num_" + id).html(num);
    }
}
function Button_plus_num(id) {
    var num = parseInt($("#show_num_" + id).html());
    var cid = parseInt($("#show_num_" + id).attr('cid'));
    var num = num + 1;
    if (num > cid) {
        var num = cid;
        $("#show_num_" + id).html(num);
    } else {
        $("#show_num_" + id).html(num);
    }
}


function Button_tijiao() {
    var data = {};
    var refund_reason = $("#selec_resason").val();
    var shenqingjine = $.trim($("#shenqingjine").val());     //　退款的订单金额
    var feedback = $("#feedback").val();
    var checkNum = /^(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))$/;

    var urlParams = parseUrlParams(window.location.href);
    var modify = urlParams['modify'];  // 是否是修改内容
    console.log(modify, 'modify');
    if (modify) {
        modify = 1;// 不是修改页面来的
    }
    else {
        modify = 0;
    }
    console.log(modify, 'modify');
    if (shenqingjine == '') {
        drawToast("您申请的金额为空哦~");
    }
    else if (!checkNum.test(shenqingjine)) {
        drawToast("您申请金额填写的不正确哦~");
    }
    else if (feedback == '') {
        drawToast("您申请建议为空,更好的有助于售后更好的服务哦~");
    }
    else {
        console.log(feedback, 'feedback');
        console.log(shenqingjine, 'shenqingjine');
        console.log(refund_or_pro, 'refund_or_pro');

        var mess = "退款金额为：" + shenqingjine + "￥" + "\n您确定退单？";
        var num = $(".order_detail_num").html();
        var oid = $(".order_detail_num").attr('id').split("_")[2];
        data = {
            'csrfmiddlewaretoken': csrftoken,
            "reason": refund_reason,
            "refund_or_pro": refund_or_pro,
            "id": oid,
            "num": num,
            "sum_price": shenqingjine,
            "feedback": feedback,
            "modify": modify
        };


        var url = GLConfig.baseApiUrl + GLConfig.refunds;
        var requetCall = function callback(res) {
            drawToast("您已经提交了申请,耐心等待售后处理！");
            console.log(",res.res", res.res);
            if (res.res == "already_refund") {
                drawToast("您已经提交了申请,耐心等待售后处理！");
                swal_flag = 0;
                //跳转到我的退货款页面
                window.location.href = "../pages/wodetuihuo.html";
            }
            else if (res.res == "refund_success") {
                drawToast("操作成功！");
                swal_flag = 0;
                //跳转到我的退货款页面
                location.href = "../pages/wodetuihuo.html";
            }
            else if (res.res == "forbidden") {
                drawToast("您的订单已经在处理中！");
                swal_flag = 0;
            }
            else if (res.res == "ok") {
                window.location.href = "../pages/wodetuihuo.html";
            }
            else if(res.res == "reject"){
                drawToast("您申请的金额，超出了实际付款，请重新填写！");
            }
        };
        if (swal_flag == 1) {
            swal({
                    title: "",
                    text: "已经提交过了哦~ 去首页逛逛?",
                    type: "",
                    showCancelButton: true,
                    imageUrl: "http://image.xiaolu.so/logo.png",
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
                    imageUrl: "http://image.xiaolu.so/logo.png",
                    confirmButtonColor: '#DD6B55',
                    confirmButtonText: "确定",
                    cancelButtonText: "取消"
                },
                function () {
                    ajax_to_server();
                }
            );
        }
        console.log("debug data :", data);
        function ajax_to_server() {
            $.ajax({
                "url": url,
                "data": data,
                "type": "post",
                dataType: 'json',
                success: requetCall
            });
        }
    }
}

function Handler_Refund_Infor(item_id, status) {// data 是订单信息
    console.log("debug item_id:", item_id, status);// 2　退款　　３是退货
    var requestUrl = GLConfig.baseApiUrl + "/products/" + item_id;
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {},
        dataType: 'json',
        success: requestCallBack
    });
    function requestCallBack(res) {
        console.log(res.is_saleopen);
        if (res.is_saleopen == false) {//商品已经下架了
            // 显示提示信息
            var html = "";
            if (status == 2) {
                html = '<span class="alert alert-danger"  >亲，此商品已特卖结束，仓储部门可能已整理好您购买的商品，装箱发货．' +
                '您的请求需要等待客服向仓储部门确认，祝您购物愉快!</span>';
            }
            //if (status == 3) {
            //     html = '<span class="" style="float:right;font-size:15px;color:red">' +
            //     '您购买的商品正在像您飞来,提交的退货请求会尽快的给您处理,还请耐心等待,祝您购物愉快!</span>';
            //}
            $(".panel-top").after(html);
        }
    }
}


