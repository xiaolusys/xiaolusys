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

function Create_detail_feiyong_dom(obj) {
    //创建订单费用信息DOM
    var feiyong = $("#feiyongdetail").html();
    return hereDoc(feiyong).template(obj);
}

function Create_refun_reason() {
    var html = $("#refund_reason").html();
    $(html).appendTo("#selec_resason");
}
function Set_order_detail(suffix) {

    //请求URL
    var requestUrl = GLConfig.baseApiUrl + suffix;
    //请求成功回调函数
    var requestCallBack = function (data) {
        if (typeof(data.id) != 'undifined' && data.id != null) {
            if (data.status == 2) { //显示申请退款标题
                console.log(data.status, '订单状态');
                var header = Create_tuikuan_header();
                $('body').before(header);  //在body 的最前面添加
            }
            else if (data.status == 3) {//显示申请退货标题
                console.log(data.status, '订单状态');
                var header = Create_tuihuo_header();
                $('body').before(header);  //在body 的最前面添加
                //添加输入　退回快递公司　　退回快递单号
                var mor_input = Create_sid_commpany();
                $("#refund_more_info").append(mor_input);
            }
            //设置订单基本信息
            var top_dom = Create_order_top_dom(data);
            $('.basic .panel-top').append(top_dom);
            //设置订单费用信息
            var feiyong_dom = Create_detail_feiyong_dom(data);
            $('.feiyong .panel-bottom').append(feiyong_dom);
            //设置订单商品明细
            $.each(data.orders,
                function (index, order) {
                    var detail_dom = Create_detail_dom(order);
                    $('.basic .panel-bottom').append(detail_dom);
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
}

function Button_reduct_num(id) {
    var num = parseInt($("#show_num_" + id).html());
    var num = num - 1;
    if (num < 0) {
        var num = 0;
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
    console.log("tijiao");

    var logi_company = $("#logi_company").val();
    var logi_sid = $("#logi_sid").val();
    console.log(logi_company, logi_sid, "快递信息");

    var data = [];
    var refund_reason = $("#selec_resason").val();
    var length = $('.goods-info').length;

    console.log("data tttt", data[0]);
    if (refund_or_pro == 1 && (logi_company == "" || logi_sid == "")) {
        // 是退货状态　　并且　快递公司或者　快递单号　有一个为空　　不执行
        if (logi_company == "") {
            alert("请填写快递公司！");
        }
        else if (logi_sid == "") {
            alert("请填写快递单号！");
        }
    }
    else {
        if (refund_or_pro == 1) {//退货　　物流信息
            data.push({
                "length": length, "reason": refund_reason,
                "refund_or_pro": refund_or_pro,
                "logi_company": logi_company,
                "logi_sid": logi_sid
            });
        }
        if (refund_or_pro == 0) {//退款
            data.push({"length": length, "reason": refund_reason, "refund_or_pro": refund_or_pro});
        }
        $('.goods-info').each(function (i, v) {
            var num = $(v).find(".order_detail_num").html();
            var oid = $(v).find(".order_detail_num").attr('id').split("_")[2];
            var gprice = ($(v).find(".gprice").html()).split(">")[2];
            var sum_price = num * gprice;
            var sub_data = {"id": oid, "num": num, "price": gprice, "sum_price": sum_price};
            data.push(sub_data);
        });
        var total_money = 0;
        for (var i = 1; i < data.length; i++) {
            var total_money = total_money + data[i].sum_price;          //总价格
        }
        console.log("total_money", total_money);
        //　退款
        var confi = confirm("退款金额为：" + total_money + "￥");
        console.log(confi);

        var url = GLConfig.baseApiUrl + GLConfig.refunds;
        if (confi) {
            //获取原因
            //ajax 请求　生成　退货款单

            function callback(res) {
                console.log(res);
                if (res.res == "already_refund") {
                    alert("您已经提交了申请,耐心等待售后处理！");
                }
                else if (res.res == "refund_success") {
                    alert("操作成功！")
                }
                else if (res.res == "forbidden") {
                    console.log(res, 'res is here ');
                    alert("您的订单已经在处理中！")
                }
            }

            $.ajax({
                "url": url,
                "data": {'csrfmiddlewaretoken': csrftoken, "refund": data},
                "type": "post",
                dataType: 'json',
                success: callback
            });
        }
    }
}




