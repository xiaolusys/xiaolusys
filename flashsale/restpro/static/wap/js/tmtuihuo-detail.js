/**
 * Created by jishu_linjie on 8/21/15.
 */
var tid = getUrlParam("tid");   //　交易id
var id = getUrlParam("id");     //　子订单id
var oid = getUrlParam("id");

var NO_REFUND = 0;                  //没有退款
var REFUND_CLOSED = 1;              //退款关闭
var REFUND_REFUSE_BUYER = 2;        //卖家拒绝退款
var REFUND_WAIT_SELLER_AGREE = 3;   //买家已经申请退款
var REFUND_WAIT_RETURN_GOODS = 4;   //卖家已经同意退款
var REFUND_CONFIRM_GOODS = 5;       //买家已经退货
var REFUND_APPROVE = 6;             //确认退款，等待返款
var REFUND_SUCCESS = 7;             //退款成功
var REFUND = 2;  // 仅仅退款　订单状态
var REFUND_PRO = 3; // 退货　订单状态
var TRADE_FINISHED = 5;
var TRADE_BUYER_SIGNED = 4;


function Create_warring_Info() { // 创建　状态　信息
    var html = $("#warring_info_content_1").html();
    return hereDoc(html);
}
function Create_warring_Info2() { // 创建　状态　信息   卖家已经同意退款
    var html = $("#warring_info_content_2").html();
    return hereDoc(html);
}
function Create_warring_Info8() { // 创建　状态　信息   卖家已经同意退款  退款　　已付款　　未发货
    var html = $("#warring_info_content_8").html();
    return hereDoc(html);
}
function Create_warring_Info3() { // 创建　状态　信息   买家已经退货
    var html = $("#warring_info_content_3").html();
    return hereDoc(html);
}

function Create_warring_Info4() { // 创建　状态　信息   卖家拒绝申请
    var html = $("#warring_info_content_4").html();
    return hereDoc(html);
}

function Create_warring_Info5() { // 创建　状态　信息   确认返款　等待返款
    var html = $("#warring_info_content_5").html();
    return hereDoc(html);
}
function Create_warring_Info6() { // 创建　状态　信息  退款成功
    var html = $("#warring_info_content_6").html();
    return hereDoc(html);
}
function Create_warring_Info7() { // 创建　状态　信息  退款成功
    var html = $("#warring_info_content_7").html();
    return hereDoc(html);
}


function Create_Info_Show() {//创建　内容　信息
    var html = $("#info_1").html();
    return hereDoc(html);
}
function Create_Info_Show2(obj) {//创建　内容　信息　卖家同意
    console.log(obj);
    var html = $("#info_2").html();
    return hereDoc(html).template(obj);
}

function Create_Info_Show3(obj) {// 创建退货中　内容　信息
    var htmlx = template("info_3", obj);// 此处使用template.js的使用方法（模板中使用if  for 等等）
    return htmlx;

}
function Create_Info_Show4() {//　创建　卖家拒绝申请　　内容
    var html = $("#info_4").html();
    return hereDoc(html);
}
function Create_Info_Show5() {//　创建　卖家正在返款到　　客户账户
    var html = $("#info_5").html();
    return hereDoc(html);
}

function Create_Info_Show6(obj) {//　创建　退款成功
    var html = $("#info_6").html();
    return hereDoc(html).template(obj);
}

function Create_Info_Show7(obj) {//　创建　退款成功
    var html = $("#info_7").html();
    return hereDoc(html).template(obj);
}

function Create_Info_Show8() {//　创建　卖家同意（已付款情况下）
    var html = $("#info_8").html();
    return hereDoc(html);
}

function Create_Btn_Modify_Refund() {//　创建  修改该btn
    var html = $("#modify_refund").html();
    return hereDoc(html);
}

function Create_Btn_Confirm_Refun() {//　创建  修改该btn
    var html = $("#btn_confirm_refund").html();
    return hereDoc(html);
}

function Create_Logistics_Dom() {//创建　退货的　输入框
    var html = $("#logistics_info").html();
    return hereDoc(html);
}

function Create_Feedback_Dom(obj) {
    var html = $("#feedback_info").html();
    return hereDoc(html).template(obj);
}

function set_Order_Detail() {

    var requestUrl = GLConfig.baseApiUrl + GLConfig.get_order_detail_url.template({"tid": tid, "oid": oid});
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {},
        dataType: 'json',
        success: requestCallBack
    });
    function requestCallBack(res) {
        console.log("debug order res:", res);
        var order_id = res.id;
        var refuUrl = GLConfig.baseApiUrl + GLConfig.refunds_by_order_id.template({"order_id": order_id});
        $.ajax({
            type: 'get',
            url: refuUrl,
            data: {},
            dataType: 'json',
            success: refundCallBack
        });

        function refundCallBack(refund) {
            console.log("debug refund: ", refund);
            console.log("debug order res refund_id:", res.refund_id);
            //
            console.log("res.refund_status:", res.refund_status);
            if (res.refund_status == 3) {  //买家申请退款
                console.log("kkk");
                if (res.status == 3 && refund.reason != "开线/脱色/脱毛/有色差/有虫洞") {
                    //已经发货 显示退货地址　如果不是质量问题　才显示
                    get_ware_by(res.item_id, res.status);//显示退货地址
                    return
                }
                var status1 = Create_Info_Show();
                $(".jifen-list").append(status1);
                var w_info = Create_warring_Info();
                $(".warring_info").append(w_info);
                bindServiceBox();
            }
            else if (res.refund_status == REFUND_WAIT_RETURN_GOODS) {  //卖家同意申请

                //　处理下　看发货仓　是哪里　显示对应退货地址
                // 这里判断下订单状态是不是已付款　　　如果是已付款不是已发货　则不显示　退货地址以及
                console.log(res.item_id, res.status);
                get_ware_by(res.item_id, res.status);
                get_refund(REFUND_WAIT_RETURN_GOODS);// 同意申请　显示feedback内容
            }
            else if (res.refund_status == 5) {// REFUND_CONFIRM_GOODS = 5  买家已经退货
                var w_info3 = Create_warring_Info3();
                $(".warring_info").append(w_info3);
                // 添加物流信息到页面
                // refunds
                var success = 0; //　仅仅表示暂时没有成功给退款
                Set_Logistic_Info(success);
            }
            else if (res.refund_status == REFUND_REFUSE_BUYER) { //卖家拒绝申请
                console.log("debug status", "卖家拒绝申请");
                //　显示 拒绝原因 显示 feedback
                get_refund(REFUND_REFUSE_BUYER);
            }
            else if (res.refund_status == REFUND_APPROVE) { //等待返款
                var w_info5 = Create_warring_Info5;
                $(".warring_info").append(w_info5);
                var approve = Create_Info_Show5();
                $(".jifen-list").append(approve);
                bindServiceBox();
            }
            else if (res.refund_status == REFUND_SUCCESS) {//　退款成功
                var w_info6 = Create_warring_Info6;
                $(".warring_info").append(w_info6);
                var success1 = 1;//表是退款成功
                Set_Logistic_Info(success1);// 设置物流信息
            }
            else if (res.refund_status == REFUND_CLOSED) {// 退款关闭
                var w_info7 = Create_warring_Info7;
                $(".warring_info").append(w_info7);
                var success2 = 2;//表是退款成功
                Set_Logistic_Info(success2);// 设置页面等信息
            }
            else{//异常状态页面
                console.log('000000000000000000000');
            }
        }
    }
}
// 访问特卖退款接口  处理　feedback 的字段给用户看，主要是因为客服审核退款的时候，要向客户解释原因．
function get_refund(state) {
    if (state == REFUND_REFUSE_BUYER) {
        var requestUrl = GLConfig.baseApiUrl + GLConfig.refunds_by_order_id.template({"order_id": oid});
        $.ajax({
            type: 'get',
            url: requestUrl,
            data: {},
            dataType: 'json',
            success: requestCallBack
        });
        var btn_modify = Create_Btn_Modify_Refund();  // 修改订单btn
        function requestCallBack(res) {
            console.log("debug res: ", res);
            var w_info4 = Create_warring_Info4;
            $(".warring_info").append(w_info4);
            var content = Create_Info_Show4();
            var feed_dom = Create_Feedback_Dom(res);
            $(".jifen-list").append(content);
            $(".buy_kefu").before(feed_dom);
            $(".content").append(btn_modify);  // 加入修改申请button
            bindServiceBox();
        }
    }
    if (state == REFUND_WAIT_RETURN_GOODS) {
        var requestUrl2 = GLConfig.baseApiUrl + GLConfig.refunds_by_order_id.template({"order_id": oid});
        $.ajax({
            type: 'get',
            url: requestUrl2,
            data: {},
            dataType: 'json',
            success: callback
        });
        function callback(res) {
            var feed_dom = Create_Feedback_Dom(res);
            $(".jifen-list").append(feed_dom);
            $(".buy_kefu").before(feed_dom);
        }
    }
}

$(document).ready(function () {
    set_Order_Detail();
});


function getUrlParam(name) {
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)"); //构造一个含有目标参数的正则表达式对象
    var r = window.location.search.substr(1).match(reg);  //匹配目标参数
    if (r != null) return unescape(r[2]);
    return null; //返回参数值
}

function Modify_Refund() {// 修改　申请
    var tid = getUrlParam("tid");
    var oid = getUrlParam("id");
    var modify = 1;
    location.href = "./tuikuan.html?oid={{ oid }}&tid={{ tid }}&modify={{ modify　}}".template({
        "oid": oid,
        "tid": tid,
        "modify": modify
    });
}

function Confirm_Refund() { //确认提交 物流信息  到　服务器
    var url = GLConfig.baseApiUrl + GLConfig.refunds;

    var modify = 2;  // 表示
    var company = $("#logi_company").val();  // 物流公司
    var sid = $("#logi_sid").val();// 快递单号
    if (company == "" || sid == "") {//物流信息不能为空　
        drawToast("物流信息不正确哦~");
        return
    }
    var data = {
        "tid": tid, "id": oid, "modify": modify, "company": company,
        "sid": sid, 'csrfmiddlewaretoken': csrftoken
    };
    swal({
            title: "",
            text: "确定提交物流信息么？",
            type: "",
            showCancelButton: true,
            imageUrl: "http://img.xiaolumeimei.com/logo.png",
            confirmButtonColor: '#DD6B55',
            confirmButtonText: "确定",
            cancelButtonText: "取消"

        },
        function () {
            $.ajax({
                "url": url,
                "data": data,
                "type": "post",
                dataType: 'json',
                success: requetCall
            });
        }
    );

    function requetCall(res) {
        if (res.res = "logistic_ok") {
            drawToast("退货信息填写成功！");
            // 重新加载页面
            window.location.reload();
        }
        else if (res.res = "not_fund") {
            drawToast("没有找到该退款单!");
        }
        else if (res.res = "order_not_fund") {
            drawToast("没有找到该订单!");
        }
        else {
            drawToast("服务器出错，请联系客服！");
        }
    }
}


function get_ware_by(item_id, order_status) {
    var requestUrl = GLConfig.baseApiUrl + "/products/" + item_id;
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {},
        dataType: 'json',
        success: requestCallBack
    });
    function requestCallBack(res) {
        console.log("res product ", res);
        var ware_by = res.ware_by;
        if (order_status == REFUND) {//退款 已付款
            var w_info8 = Create_warring_Info8();// 创建退款的显示信息
            $(".warring_info").append(w_info8);
            var success_yifuk = Create_Info_Show8();
            $(".jifen-list").append(success_yifuk);
            bindServiceBox();
        }
        if (order_status == REFUND_PRO || order_status == TRADE_FINISHED || order_status == TRADE_BUYER_SIGNED) {
            //退货　已经发货 或者交易成功 或者是货到付款签收　　都显示退货地址
            var w_info2 = Create_warring_Info2();//创建退货成功的显示信息
            $(".warring_info").append(w_info2);

            if (ware_by == 0) {
                console.log('没有分仓');//
                Create_ware_by_address(None_ADDRESS);
            }
            if (ware_by == SHANG_HAI) {
                console.log('上海仓');//
                Create_ware_by_address(SHANG_HAI);
            }
            if (ware_by == GUANG_ZHOU) {
                console.log('广州仓');//
                Create_ware_by_address(GUANG_ZHOU);
            }
            var logistics = Create_Logistics_Dom();// 填充物流信息输入框　　判断是否是退货　否则没有输入框
            $(".jifen-list").append(logistics);
            var btn_confirm_refund = Create_Btn_Confirm_Refun();// 确认提交物流信息btn
            $(".content").append(btn_confirm_refund); // 添加　提交退货
        }
    }
}
var None_ADDRESS = 0;
var SHANG_HAI = 1;
var GUANG_ZHOU = 2;

function Create_ware_by_address(address) {
    var html = "";
    if (address == SHANG_HAI) {
        console.log("上海仓库显示");
        html = {"ware_by_address": $("#shanghai_address").html()};
    }
    else if (address == GUANG_ZHOU) {
        console.log("上海仓库显示");
        html = {"ware_by_address": $("#guangzhou_address").html()};
    }
    else {
        html = {
            ware_by_address: "请联系客服索要退货地址,正确填写快递公司和退货地址," +
            "有助我们更快的帮您处理退货退款问题,祝你购物愉快~"
        };
    }
    var status2 = Create_Info_Show2(html);
    $(".jifen-list").append(status2);
    bindServiceBox();
}

function Set_Logistic_Info(success) {
    // 设置　物流信息
    console.log('debug　退货中．．．');
    var requestUrl = GLConfig.baseApiUrl + GLConfig.refunds;
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {},
        dataType: 'json',
        success: requestCallBack
    });
    function requestCallBack(res) {// res 对应该用户的在pay 中的退货款单
        var tid = getUrlParam("tid");   //　交易id
        var id = getUrlParam("id");     //　子订单id
        var oid = getUrlParam("id");
        console.log('oid', oid);
        console.log("debug refund res results :", res.results);
        for (var i = 0; i < res.results.length; i++) {
            console.log(res.results[i].order_id, oid);
            if (res.results[i].order_id == oid) {

                //　退货中信息
                var refund_no = res.results[i].refund_no;
                var company_name = res.results[i].company_name;
                var sid = res.results[i].sid;
                var created = res.results[i].created;
                var refund_fee = res.results[i].refund_fee;
                var desc = res.results[i].desc;

                //　退款成功信息
                var reason = res.results[i].reason; // 退款原因
                var title = res.results[i].title; //商品标题

                var obj = {};
                if (success == 1) {
                    obj = {
                        "refund_no": refund_no, "company_name": company_name, "reason": reason, "title": title,
                        "sid": sid, "created": created, "refund_fee": refund_fee, "desc": desc
                    };
                    var info6 = Create_Info_Show6(obj);
                    $(".jifen-list").append(info6);
                    bindServiceBox();
                }
                else if (success == 2) {
                    obj = {
                        "reason": reason, "created": created, "refund_fee": refund_fee, "desc": desc
                    };
                    var info7 = Create_Info_Show7(obj);
                    $(".jifen-list").append(info7);
                    bindServiceBox();
                }
                else {
                    obj = {
                        "refund_no": refund_no, "company_name": company_name,
                        "sid": sid, "created": created, "refund_fee": refund_fee, "desc": desc
                    };
                    var info3 = Create_Info_Show3(obj);
                    $(".jifen-list").append(info3);
                    bindServiceBox();
                }
            }
        }
    }
}


function bindServiceBox() {
    $('.service_box').click(function () {
        DoIfLogin({
            callback: function () {
                var trade_id = getUrlParam('tid');
                var requestUrl = GLConfig.baseApiUrl + GLConfig.get_trade_details_url.template({"trade_id": trade_id});
                $.ajax({
                    type: 'get',
                    url: requestUrl,
                    data: {},
                    dataType: 'json',
                    success: requestCallBack
                });
                function requestCallBack(res) {
                    var params = {
                        'orderid': res.tid,
                        'profile': JSON.parse(getCookie(PROFILE_COOKIE_NAME) || '{}')
                    };
                    loadNTalker(params, callNTKFChatPage);
                }
            },
            redirecto: window.location.href
        });
    });
}

function callNTKFChatPage() {
    //对应手机WAP端组代码
    NTKF.im_openInPageChat("kf_9645_1444459002183");
}