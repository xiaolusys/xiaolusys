/**
 *@author: imeron
 *@date: 2015-07-22
 */
var time_interval_id = null;

function parseTimeSM(start_time) {
    //将时间差格式化成字符串[分:秒]
    var d1 = new Date(start_time);
    var d2 = new Date();
    var time_delta = parseInt((d2.getTime() - d1.getTime()) / 1000);
    var time_alias = GLConfig.order_expired_in - time_delta;
    if (time_alias < 0) {
        return '00:00';
    }
    var minute = parseInt(time_alias / 60);
    var second = parseInt(time_alias % 60);
    return (minute < 10 ? '0' + minute : minute.toString()) + ':' + (second < 10 ? '0' + second : second.toString())
}

function setOrderTimeInterval() {
    var has_period = false;
    $('.shengyu').each(function (index, e) {
        var created_str = $(e).attr('xl_created');
        var time_str = parseTimeSM(created_str);
        $(e).html('剩余时间：' + time_str);
        if (time_str != '00:00') {
            has_period = true
        }
    });
    //如果页面没有需要更新的计时任务则退出
    if (!has_period) {
        clearInterval(time_interval_id);
        return;
    }
}

function Create_order_dom(obj) {
    //创建特卖订单DOM
    obj.created = obj.created.replace(/[TZ]/g, ' ').replace(/-/g, '/')
    console.log('obj.created', obj.created);
    if (obj.status == 1) {
        obj.btn_class = 'shengyu';
        obj.btn_content = '剩余时间：' + parseTimeSM(obj.created);
    }
    //else if (obj.status == 3) {// 已发货才显示确认签收
    //    obj.btn_class = 'btn-qianshou';
    //    obj.btn_content = '确认签收';
    //    obj.cid = obj.id;
    //} else {
    //    obj.btn_class = '';
    //    obj.btn_content = '';
    //}
//<div class="{{btn_class}}" xl_created="{{created}}" cid="{{cid}}" onclick="Confirm_Sign_For(this)">{{btn_content}}</div>

    function Order_dom() {
        /*
         <li>
         <div class="top clear">
         <div class="xiadan">下单时间：{{ created }}</div>
         </div>
         <a href="./dd-detail.html?id={{ id }}" class="info clear">
         <div class="left"><img src="{{ order_pic }}?imageMogr2/thumbnail/150/format/jpg/quality/90" /></div>
         <div class="right">
         <p>订单编号：<span class="caaaaaa orderno">{{ tid }}</span></p>
         <p>订单状态：<span class="caaaaaa">{{ status_display }}</span></p>
         <p>订单金额：<span class="cf353a0"><em>¥</em>{{ payment }}</span></p>
         </div>
         </a>
         </li>
         */
    };
    return hereDoc(Order_dom).template(obj)
}

function Set_orders(suffix) {
    //请求URL
    var requestUrl = GLConfig.baseApiUrl + suffix;
    //请求成功回调函数
    var requestCallBack = function (data) {
        if (!isNone(data.count) && data.count > 0) {
            $.each(data.results,function (index, order) {
                    var order_dom = Create_order_dom(order);
                    $('.order_ul').append(order_dom);
                }
            );
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

    //设置订单剩余时间更新
    time_interval_id = setInterval(setOrderTimeInterval, 1000);
}

function Create_order_top_dom(obj) {
    var html = template("top_template", obj);
    return html;
}
function Create_button_buy_dom() {
    var html = $('#button_buy').html();
    return hereDoc(html);
}
function Create_detail_dom(obj) {
    var html = template('top_detail_template',obj);//.html();
    //return hereDoc(html).template(obj);
    return html
}

function Create_detail_shouhuo_dom(obj) {
    //创建订单收货信息DOM
    var html = $('#shouhuo_template').html();
    return hereDoc(html).template(obj);
}

function Create_detail_feiyong_dom(obj) {
    //创建订单费用信息DOM
    var html = $('#shoufei_template').html();
    return hereDoc(html).template(obj);
}


function Set_order_detail(suffix) {
    //请求URL
    var requestUrl = GLConfig.baseApiUrl + suffix;
    //请求成功回调函数
    var requestCallBack = function (data) {
    	//设置订单商品明细
        if (!isNone(data.orders)){
	        $.each(data.orders,function (index, order) {
                    if(order.kill_title == true){
                        order.kill_title=1;
                    }
                    else{
                            order.kill_title=0;
                        }
	                order.trade_id = suffix.split("/")[2];//赋值交易id
	                var detail_dom = Create_detail_dom(order);
	                $('.basic .panel-bottom').append(detail_dom);
	        });
	    }else{
	    	data.order_total_price = data.order_total_price / 100;
	    	data.order_express_price = data.order_express_price / 100;
	    	var detail_dom = Create_detail_dom(data);
	        $('.basic .panel-bottom').append(detail_dom);
	    }
        //设置订单基本信息
        var top_dom = Create_order_top_dom(data);
        $('.basic .panel-top').append(top_dom);
        //设置订单收货信息
        var shouhuo_dom = Create_detail_shouhuo_dom(data);
        $('.shouhuo .panel-bottom').append(shouhuo_dom);
        //设置订单费用信息
        var feiyong_dom = Create_detail_feiyong_dom(data);
        $('.feiyong .panel-bottom').append(feiyong_dom);

        Cancel_order(suffix);//页面加载完成  调用 取消订单功能
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

// 订单状态显示　跳转处理　已经　确认签收处理
function Order_Status_Handdler(trade_id, id, status, refund_status, kill_title) {
    if(kill_title){
        drawToast("秒杀订单不可退款，如疑问请联系客服！");
        return
    }
    if (status == 2 && refund_status == 0) { //　已经付款　没有退款　跳转到退款　页面
        console.log("跳转到退款页面");
        location.href = 'tuikuan.html?oid=' + id + '&tid=' + trade_id;
    }
    if (status == 3 && refund_status == 0) {
        console.log("确认签收");
        Confirm_Sign_For(id);// 对一笔订单进行签收
    }
    if (status == 4 && refund_status == 0) { //　已经签收　没有退款　跳转到退款　页面
        console.log("跳转到退款页面");
        location.href = 'tuikuan.html?oid=' + id + '&tid=' + trade_id;
    }
    if (status == 5 && refund_status == 0) { //　交易成功
        console.log("交易成功");
        drawToast("您的订单已经交易成功,如需申请退货请联系客服！");
    }
}

function Cancel_order(suffix) {
    // 取消订单
    var cid = $(".btn_interactive").attr('cid');
    if (cid == 0 || cid == 1) {
        var buy_button = Create_button_buy_dom();
        $('.buy_button').append(buy_button);
        $(".btn_interactive").removeAttr('href');  //删除退款跳转的链接 防止跳转到 退款页面
    }
    $(".btn_interactive").click(function () {
        var cid = $(this).attr('cid');
        var mess = "取消的产品可能被别人抢走哦～ \n要取消么";
        swal({
            title: "小鹿美美",
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
        });
        function ajax_to_server (){ // 确定则取消
            if ($("#status_display").html() == "交易关闭") {
                drawToast("交易已经取消啦~");
            }
            else if (cid == 0 || cid == 1) {        //订单创建 或者 待付款  允许取消订单
                var cancel_bt = $(".btn_interactive");
                //取消订单
                var arr = suffix.split('/'); //分割字符串获取订单id  /trades/78/orders/details.json
                var requestUrl = GLConfig.baseApiUrl + GLConfig.delete_detail_trade.template({"trade_id": arr[2]});
                ///rest/v1/trades/77  请求的地址
                if (cancel_bt.hasClass('loading')) {
                    return;
                }
                cancel_bt.addClass('loading');
                function requestCallBack(res) {
                    if (res['ok']) {
                        $("#status_display").html("交易关闭");
                        drawToast("交易已经取消！");
                        //删除取消退款的button
                        $(".btn-quxiao").remove();
                        //删除最下方购买button
                        $(".btn-buy").remove();
                        //刷新页面
                        location.reload()
                    }
                    else {
                        drawToast("取消失败，请尝试刷新页面！");
                    }
                }

                $.ajax({
                    type: 'post',
                    url: requestUrl,
                    data: {'csrfmiddlewaretoken': csrftoken, '_method': 'DELETE'},//封装请求要求的request.data
                    dataType: 'json',
                    success: requestCallBack
                });
            }
            else {

            }
        }
    });
}

//确认签收
function Confirm_Sign_For(oid) {
    var requestUrl = GLConfig.baseApiUrl + GLConfig.confirm_sign_order.template({"order_id": oid});
    swal({
            title: "",
            text: "订单准备签收啦~ 确认收货么？",
            type: "",
            showCancelButton: true,
            imageUrl: "http://img.xiaolumeimei.com/logo.png",
            confirmButtonColor: '#DD6B55',
            confirmButtonText: "确定",
            cancelButtonText: "取消"
        },
        function (){
            confirm_Sign_For();
        }
    );
    function requestCallBack(res){
        if(res.ok){
            //签收成功 则 刷新页面
            location.reload();
        }
        else{
            drawToast("签收出现了问题，请联系客服咯~");
        }
    }

    function confirm_Sign_For() {
        $.ajax({
            type: 'post',
            url: requestUrl,
            data: {'csrfmiddlewaretoken': csrftoken, '_method': 'POST'},//封装请求要求的request.data
            dataType: 'json',
            success: requestCallBack
        });
    }
}


function Wuliu(tid) {
    //获取物流信息
    //alert(urlParams['id'])
    var requestUrl = "/rest/wuliu/";
    var requestCallBack = function(info) {
        //alert(ret);
        console.log("debug wuliu:",info);
        if (info.response_content.result) {

            if (parseInt(info.response_content.ret.status) > 1) {
                var data1 = info.response_content.ret.data;
                if (data1.length > 2) {
                    for (var i = data1.length - 2; i < data1.length; i++) {
                        if (i > data1.length - 2) {
                            var address = "<li> <p class='text'>" + data1[i].content + "</p><p class='time'>" + data1[i].time + "</p><div class='dotted'></div></li><li></li>";
                            $(".step-list").append(address);
                        } else {
                            var address = "<li> <p class='text'>" + data1[i].content + "</p><p class='time'>" + data1[i].time + "</p><div class='dotted'></div></li>";
                            $(".step-list").append(address);
                        }
                    }
                } else {
                    for (var i = 0; i < data1.length; i++) {
                        var address = "<li> <p class='text'>" + data1[i].content + "</p><p class='time'>" + data1[i].time + "</p><div class='dotted'></div></li><li></li>";
                        $(".step-list").append(address);
                    }
                }
            }
            //针对有物流单，暂时没有数据
            else if (parseInt(info.response_content.ret.status) == 1) {
                //加上前一个状态，就是配货
                var address = " <li><p class='text'>您的商品配货完成</p><p class='time'>" + info.response_content.create_time + "</p><div class='dotted'></div> </li>";
                $(".step-list").append(address);
                var address = " <li><p class='text'>您的商品已出库</p><p class='time'>" + info.response_content.time + "</p><div class='dotted'></div> </li><li></li>";
                $(".step-list").append(address);
            }
            //根据从数据库来查询的数据的格式
            else {
                var data1 = info.response_content.ret;
                if (data1.length > 2) {
                    for (var i = data1.length - 2; i < data1.length; i++) {
                        if (i > data1.length - 2) {

                            var address = "<li> <p class='text'>" + data1[i].content + "</p><p class='time'>" + data1[i].time + "</p><div class='dotted'></div></li><li></li>";
                            $(".step-list").append(address);
                        } else {
                            var address = "<li> <p class='text'>" + data1[i].content + "</p><p class='time'>" + data1[i].time + "</p><div class='dotted'></div></li>";
                            $(".step-list").append(address);
                        }
                    }
                } else {
                    for (var i = 0; i < data1.length; i++) {
                        var address = "<li> <p class='text'>" + data1[i].content + "</p><p class='time'>" + data1[i].time + "</p><div class='dotted'></div></li><li></li>";
                        $(".step-list").append(address);
                    }
                }
            }
        }

        else {
            var address = " <li><p class='text'>" + info.response_content.message + "</p><p class='time'>" + info.response_content.time + "</p><div class='dotted'></div> </li><li></li>";
            $(".step-list").append(address);
        }
    }
    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {
            'tid': tid
        },
        dataType: 'json',
        success: requestCallBack
    });
}