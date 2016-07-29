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

            var cart_ids = getUrlParam('cart_ids');//获取购物车的ids
            var item_id = getUrlParam('item_id');// 获取购买产品
            var sku_id = getUrlParam('sku_id');// 获取购买产品

            var mm_linkid = getUrlParam('mm_linkid');
            var ufrom = getUrlParam('ufrom');

            console.log("cart_ids :", cart_ids);
            console.log("item_id :", item_id);

            if (cart_ids) {
                var choose_coupon_url = "./choose-coupon.html?cart_ids=" + cart_ids;
                if (mm_linkid != null) {
                    choose_coupon_url += "&mm_linkid=" + mm_linkid;
                }
                if (ufrom != null) {
                    choose_coupon_url += "&ufrom=" + ufrom;
                }
                location.href = choose_coupon_url;
            }
            else if (item_id) {
                var pro_num = document.getElementsByName("num")[0].value;
                var chosse_url = "./choose-coupon.html?item_id=" + item_id + "&pro_num=" + pro_num + "&sku_id=" + sku_id;

                if (mm_linkid != null) {
                    chosse_url += "&mm_linkid=" + mm_linkid;
                }
                if (ufrom != null) {
                    chosse_url += "&ufrom=" + ufrom;
                }
                location.href = chosse_url
            }
            else {
                //var total_money = ($("#total_money").html().split(">")[2]);
                //var pro_num = document.getElementsByName("num")[0].value;
                //console.log("pro_num :", pro_num);
                //if (mm_linkid != null) {
                //    new_url += "&mm_linkid=" + mm_linkid;
                //}
                //if (ufrom != null) {
                //    new_url += "&ufrom=" + ufrom;
                //}
                //location.href = "./choose-coupon.html?price=" + total_money + "&pro_num=" + pro_num + "&item_id=" + item_id;
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
            imageUrl: "http://img.xiaolumeimei.com/logo.png",
            confirmButtonColor: '#DD6B55',
            confirmButtonText: "确定",
            cancelButtonText: "取消"
        },
        function () {//确定　则跳转
            console.log(document.referrer);
            // 如果是购物车来
            var mm_linkid = getUrlParam('mm_linkid');
            var ufrom = getUrlParam('ufrom');
            console.log(document.referrer.indexOf('cart_ids'),'debug problem ');
            if (document.referrer.indexOf('cart_ids') >= 0) {
                var cart_ids = getUrlParam('cart_ids');
                var new_url = document.referrer.split("cart_ids")[0] + 'cart_ids=' + cart_ids + '&coupon_id=' + coupon_id;
                if (mm_linkid != null) {
                    new_url += "&mm_linkid=" + mm_linkid;
                }
                if (ufrom != null) {
                    new_url += "&ufrom=" + ufrom;
                }
                location.href = new_url;
            }
            else {//　否则
                var item_id = getUrlParam('item_id');
                var pro_num = getUrlParam('pro_num');
                var sku_id = getUrlParam('sku_id');

                var buy_nuw_url = document.referrer.split("item_id")[0] + "item_id=" + item_id +
                    '&pro_num=' + pro_num + "&coupon_id=" + coupon_id + '&sku_id=' + sku_id;

                if (mm_linkid != null) {
                    buy_nuw_url += "&mm_linkid=" + mm_linkid;
                }
                if (ufrom != null) {
                    buy_nuw_url += "&ufrom=" + ufrom;
                }
                location.href = buy_nuw_url;
            }
        });
}
function choose_Coupon(coupon_id, coupon_type) {
    var pro_num = parseFloat(getUrlParam('pro_num'));
    var item_id = parseInt(getUrlParam('item_id'));
    var cart_ids = getUrlParam('cart_ids');
    console.log("pro_num",pro_num, "item_id",item_id,'cart_ids',cart_ids, isNaN(item_id));
    console.log("choose coupon_type:", coupon_type);
    var couponUrl = GLConfig.baseApiUrl + GLConfig.choose_coupon.template({"coupon_id": coupon_id});
    var data = {};
    if (isNaN(item_id)||isNaN(pro_num)) {
        if(!cart_ids){
            drawToast('页面异常');
        }
    }
    if(cart_ids){
        data = {"cart_ids": cart_ids};
    }
    else {
        data = {"pro_num": pro_num, "item_id": item_id};
    }
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
        if (res.res == 0) {
            copon_judeg(coupon_id, pro_num);
        }
        else if(res.res == 1) {
            drawToast(res.coupon_message);
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
            imageUrl: "http://img.xiaolumeimei.com/logo.png",
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