/**
 * Created by jishu_linjie on 8/17/15.
 */
var RELEASE = 1;
var PAST = 2;
var USED = 1;
var UNUSED = 0;
function checkout_Recharge_Product() {
    var sku_id = getUrlParam("sku_id");//商品id
    var array = ["86345", "86346", "86347"];
    var isin = $.inArray(sku_id, array);
    if (isin != -1) {// 如果检测到是充值产品的页面　直接删除　dom 返回
        $(".coupons").remove();
        return true
    }
}

function get_Coupon_On_Buy() {
    var judge = checkout_Recharge_Product();
    if (judge == true) {
        return
    }
    var url = GLConfig.baseApiUrl + GLConfig.usercoupons;
    $.get(url, function (res) {
        console.log("user_coupons: ", res);
        Coupon_Nums_Show(res.count);//显示优惠券数量
    });
}

function Coupon_Nums_Show(nums) {
    console.log('nums nums ', nums);
    $("#coupon_nums").text("可用优惠券（" + nums + "）");
    if (nums > 0) {
        $("#coupon_nums").click(function () {
            //判断是否是确认页面

            var cart_ids = getUrlParam('cart_ids');
            console.log(cart_ids);
            if (cart_ids) {
                var total_money = ($("#total_money").html().split(">")[2]);
                var pro_num = $(".pro_num").html();
                console.log("pro_num :", pro_num, total_money);
                location.href = "./choose-coupon.html?price=" + total_money + "&pro_num=" + pro_num;
            }
            else {
                var total_money = ($("#total_money").html().split(">")[2]);
                var pro_num = document.getElementsByName("num")[0].value;
                console.log("pro_num :", pro_num);
                location.href = "./choose-coupon.html?price=" + total_money + "&pro_num=" + pro_num;
            }
        });
    }
}
var pageNumber = 1;
function get_Coupon_On_Choose() {
    var url = GLConfig.baseApiUrl + GLConfig.usercoupons + "?page=" + pageNumber;
    $.get(url, function (res) {
        console.log("debug choose coupon:", res);
        if (res.count > 0) {
            $.each(res.results, function (i, val) {
                if (val.status == UNUSED && val.poll_status == RELEASE) {
                    var c_valid = create_valid(val);
                    $('.youxiao').append(c_valid);
                }
                else if (val.poll_status == RELEASE && val.status == USED) {
                    var c_not_valid = create_not_valid(val);
                    $('.shixiao').append(c_not_valid);
                }
            });
        }
        else {
            // 显示提示信息　没有优惠券
            pop_info();
        }
        pageNumber += 1;
    });
}

function create_valid(obj) {
    var c_valid = $("#c_valid").html();
    return hereDoc(c_valid).template(obj)
}
function create_not_valid(obj) {
    var c_not_valid = $("#c_not_valid").html();
    return hereDoc(c_not_valid).template(obj)
}
function create_past(obj) {
    var c_past = $("#c_past").html();
    return hereDoc(c_past).template(obj)
}

function copon_judeg(coupon_id, pro_num) {
    swal({
            title: "",
            text: '确定选择这张优惠券吗？',
            type: "",
            showCancelButton: true,
            imageUrl: "http://image.xiaolu.so/logo.png",
            confirmButtonColor: '#DD6B55',
            confirmButtonText: "确定",
            cancelButtonText: "取消"
        },
        function () {//确定　则跳转
            console.log(document.referrer);
            var buy_nuw_url = document.referrer.split("&")[0] + "&" + document.referrer.split("&")[1];
            var include_coupon = buy_nuw_url + "&coupon_id=" + coupon_id + "&pro_num=" + pro_num;
            location.href = include_coupon;
        });
}
function choose_Coupon(coupon_id, coupon_type) {
    var price = parseFloat(getUrlParam('price'));
    var pro_num = parseFloat(getUrlParam('pro_num'));
    console.log("choose coupon_type:", coupon_type);
    var couponUrl = GLConfig.baseApiUrl + GLConfig.choose_coupon.template({"coupon_id": coupon_id});
    var data = {"price": price, "pro_num": pro_num};
    $.ajax({
        "url": couponUrl,
        "data": data,
        "type": "post",
        dataType: 'json',
        success: couponcallback,
        error: function (err) {
            var resp = JSON.parse(err.responseText);
            if (!isNone(resp.detail)) {
                drawToast(resp.detail);
            }
        }
    });
    function couponcallback(res) {
        console.log(res);
        if (res.res == 'ok') {
            copon_judeg(coupon_id, pro_num)
        }
    }
}
function set_pro_num() {
    var pro_num_s = getUrlParam('pro_num');
    if (pro_num_s == null) {
        pro_num_s = 1;
    }
    var pro_num = parseFloat(pro_num_s);
    var sku_id = parseFloat(getUrlParam('sku_id'));
    var num_d = $("#num_" + sku_id);
    num_d.val(pro_num);
}

function getUrlParam(name) {
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)"); //构造一个含有目标参数的正则表达式对象
    var r = window.location.search.substr(1).match(reg);  //匹配目标参数
    if (r != null) return unescape(r[2]);
    return null; //返回参数值
}

function pop_info() {
    // 显示提示信息　没有优惠券
    swal({
            title: "",
            text: '您暂时还没有优惠券哦~',
            type: "",
            showCancelButton: false,
            imageUrl: "http://image.xiaolu.so/logo.png",
            confirmButtonColor: '#DD6B55',
            confirmButtonText: "返回",
            cancelButtonText: "取消"
        },
        function () {//确定　则跳转
            location.href = document.referrer;
        });
}

function loadData(func) {//动态加载数据
    var totalheight = parseFloat($(window).height()) + parseFloat($(window).scrollTop());//浏览器的高度加上滚动条的高度
    if ($(document).height() - 5 <= totalheight)//当文档的高度小于或者等于总的高度的时候，开始动态加载数据
    {
        func();
    }
}