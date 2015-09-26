/**
 * Created by jishu_linjie on 8/17/15.
 */

function get_Coupon_On_Buy() {
    var url = GLConfig.baseApiUrl + GLConfig.usercoupons;
    $.get(url, function (res) {
        if (res.length > 0) {
            var nums = 0;
            $.each(res, function (i, val) {
                console.log("debug coupon status:", val.status);
                if (val.status == 0) {
                    nums = nums + 1;//有效可用的优惠券数量
                }
            });
            Coupon_Nums_Show(nums);//显示优惠券数量
        }
        else if (res.length == 0) {
            Coupon_Nums_Show(0);//显示优惠券数量
        }
    });
}

function Coupon_Nums_Show(nums) {
    console.log('nums nums ', nums);
    $("#coupon_nums").text("可用优惠券（" + nums + "）");
    if (nums > 0) {
        $("#coupon_nums").click(function () {
            var total_money = ($("#total_money").html().split(">")[2]);
            var pro_num = document.getElementsByName("num")[0].value;
            console.log("pro_num :", pro_num);
            location.href = "./choose-coupon.html?price=" + total_money+"&pro_num=" + pro_num;
        });
    }
}

function get_Coupon_On_Choose() {
    var url = GLConfig.baseApiUrl + GLConfig.usercoupons;
    $.get(url, function (res) {
        console.log("debug choose coupon:", res);
        if (res.length > 0) {
            $.each(res, function (i, val) {
                if (val.status == 0) {
                    var c_valid = create_valid(val);
                    $('.coupons').append(c_valid);
                }
                if (val.status == 1) {
                    var c_not_valid = create_not_valid(val);
                    $('.coupons').append(c_not_valid);
                }
            });
        }
        else {
            // 显示提示信息　没有优惠券
            pop_info();
        }
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
    if (coupon_type == 0 && price >= 30) {
        copon_judeg(coupon_id, pro_num)
    }
    else if (coupon_type == 2 && price >= 150) {//这里判断要满150
        copon_judeg(coupon_id, pro_num)
    }
    else if (coupon_type == 3 && price >= 259) {//这里判断要满259
        copon_judeg(coupon_id, pro_num)
    }
    else {
        drawToast("商品价格不足优惠券使用金额哦~");
    }
}
function set_pro_num(){
    var pro_num_s = getUrlParam('pro_num');
    if (pro_num_s == null) {
        pro_num_s = 1;
    }
    var pro_num = parseFloat(pro_num_s);
    var sku_id = parseFloat(getUrlParam('sku_id'));
    var num_d = $("#num_"+sku_id);
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