/**
 *@author: imeron
 *@date: 2015-07-22
 */
//字符串模板
String.prototype.template = function (data) {
    var str = this;
    if (data && data.sort) {
        for (var i = 0; i < data.length; i++) {
            str = str.replace(new RegExp("{\\{" + i + "}}", "gm"), data[i]);
        }
        return str;
    }

    var placeholder = str.match(new RegExp("{{.+?}}", 'ig'));
    if (data && placeholder) {
        for (var i = 0; i < placeholder.length; i++) {
            var key = placeholder[i];
            var value = proxy.call(data, key.replace(new RegExp("[{,}]", "gm"), ""));
            key = key.replace(new RegExp("\\\.", "gm"), "\\.").replace("{{", "{\\{");
            if (value == null)
                value = "&nbsp;";
            str = str.replace(new RegExp(key, "gm"), value);
        }
    }
    return str;

    function proxy(key) {
        try {
            return eval('this.' + key);
        } catch (e) {
            return "";
        }
    }
};
//判断是否为空
function isNone(value) {
    return typeof(value) == 'undifined' || value == null
}

function parseUrlParams(myUrl) {
    var vars = [], hash;
    var hashes = window.location.href.slice(myUrl.indexOf('?') + 1).split('&');
    for (var i = 0; i < hashes.length; i++) {
        hash = hashes[i].split('=');
        vars.push(hash[0]);
        vars[hash[0]] = hash[1];
    }
    return vars;
}

//定义多行字符串函数实现
function hereDoc(f) {
    return f.toString().replace(/^[^\/]+\/\*!?\s?/, '').replace(/\*\/[^\/]+$/, '');
}

//设置初始页面VIEWPORT
(function () {
    var oViewport = document.getElementById('viewport');
    var phoneWidth = parseInt(window.screen.width);
    var phoneScale = phoneWidth / 640;
    var ua = navigator.userAgent;
    if (/Android (\d+\.\d+)/.test(ua)) {
        var version = parseFloat(RegExp.$1);
        if (version > 2.3) {
            oViewport.setAttribute('content', 'width=640, minimum-scale = ' + phoneScale + ', maximum-scale = ' + phoneScale + ', target-densitydpi=device-dpi')
        } else {
            oViewport.setAttribute('content', 'width=640, target-densitydpi=device-dpi');
        }
    } else {
        oViewport.setAttribute('content', 'width=640, user-scalable=no, target-densitydpi=device-dpi');
    }
    window.onload = function () {
        document.body.addEventListener('touchstart', function () {});
        if (window.navigator.standalone) jQuery.ajaxSetup({isLocal:true});
    }
})();

//全局配置
var GLConfig = {
	user_profile:null,
	baseApiUrl:'/rest/v1', //API接口调用前缀
	order_expired_in:20 * 60,//expired time
	login_url:'/pages/denglu.html',//登录URL
	zhifucg_url:'/pages/zhifucg.html',//支付成功跳转URL
	daizhifu_url:'daizhifu-dd.html',//待支付订单页面
	today_suffix:'today',  //获取首页今日商品信息，URL标识
	previous_suffix:'previous', //获取首页昨日商品信息，URL标识
	get_childlist_url:'/products/childlist.json', //获取潮流童装商品列表
	get_ladylist_url:'/products/ladylist.json', //获取时尚女装商品列表
	get_modellist_url:'/products/modellist/{{model_id}}.json', //获取同款商品列表
	get_product_detail_url:'/products/{{product_id}}/details.json', //获取商品明细
	get_trade_all_url:'/trades.json', //获取用户所有订单
	get_trade_waitpay_url:'/trades/waitpay.json', //获取用户待付款订单
	get_trade_waitsend_url:'/trades/waitsend.json', //获取用户待发货订单
	get_trade_details_url:'/trades/{{trade_id}}/orders/details.json', //获取订单明细
    get_order_detail_url:'/trades/{{ tid }}/orders/{{ oid　}}',//获取单个SaleOrder明细
	get_trade_charge_url:'/trades/shoppingcart_create.json', //购物车结算订单接口
	get_buynow_url:'/trades/buynow_create.json', //立即购物订单创建接口
	waitpay_charge:'/trades/{{trade_id}}/charge.json', //待支付订单结算接口
	get_cart_url:'/carts.json', //获取购物车详细
	get_cart_payinfo_url:'/carts/carts_payinfo.json?cart_ids={{cart_ids}}', //根据购物车id列表获取支付明细
	get_now_payinfo_url:'/carts/now_payinfo.json?item_id={{item_id}}&sku_id={{sku_id}}', //根据购物车id列表获取支付明细
	get_num_cart:'/carts/show_carts_num?format=json', //获取购物车数量
	get_plus_skunum_url:'/carts/sku_num_enough.json', //添加订单数量接口
	get_all_address:'/address.json',//获取个人用户地址列表
	get_user_address:'/address.json',//获取个人用户地址列表
	change_default:'/address/change_default/?format=json',//更改默认地址
	province_list:'/districts/province_list?format=json',//省份列表
	city_list:'/districts/city_list?format=json',//城市列表
	country_list:'/districts/country_list?format=json',//区/县列表
	create_address:'/address/create_address?format=json',//创建新的收货地址
	update:'/address/update/?format=json',//修改收货地址
	get_user_profile:'/users/profile.json',//得到用户信息
	get_user_point:'/integral.json',//得到用户积分
	delete_detail_trade:'/trades/{{trade_id}}',//用户取消订单
	user_logout:'/users/customer_logout',//用户注销
	user_islogin:'/users/islogin.json',//用户是否登录
    refunds:'/refunds'//退款
};

// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');


/*
 * 模拟toast
 * auther:yann
 * date:2015/30/7
 */
var intervalCounter = 0;
function hideToast() {
    var alert = document.getElementById("toast");
    alert.style.opacity = 0;
    alert.style.zIndex = -9999;
    clearInterval(intervalCounter);
}
function drawToast(message) {
    var alert = document.getElementById("toast");
    if (alert == null) {
        var toastHTML = '<div id="toast">' + message + '</div>';
        document.body.insertAdjacentHTML('beforeEnd', toastHTML);
    }
    else {
        alert.innerHTML = message;
        alert.style.opacity = .9;
        alert.style.zIndex = 9999;
    }
    console.log('debug toast:', alert);
    intervalCounter = setInterval("hideToast()", 2000);
}

function DoIfLogin(cfg){
	$.ajax({
        type: 'get',
        url: GLConfig.baseApiUrl + GLConfig.user_islogin,
        data: "",
        success: cfg.callback,
        error: function (data) {
        	console.log('debug login:',data);
            if (data.status == 403) {
                window.location = GLConfig.login_url+'?next='+encodeURIComponent(cfg.redirecto);
            }
        }
    });
}



var remain_date = 0;

function Set_shopcarts_num() {
    /*
     * 得到购物车数量
     * auther:yann
     * date:2015/30/7
     */
    var requestUrl = GLConfig.baseApiUrl + GLConfig.get_num_cart;
    var requestCallBack = function (res) {
        $(".total").html(res.result);
        var newDate = new Date();
        if (res.last_created > 0) {
            remain_date = newDate.setTime(res.last_created * 1000);
            cart_timer.publicMethod();
        }

    };
    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: "",
        success: requestCallBack,
        error: function (data) {
            console.log('debug cartnum:', data);
            if (data.status == 403) {
                $(".total").html("0");
            }
        }
    });
}

var cart_timer = function () {
    /*
     * 购物车倒计时
     * auther:yann
     * date:2015/14/8
     */
    function privateFunction() {
        var ts = remain_date - (new Date());//计算剩余的毫秒数
        var mm = parseInt(ts / 1000 / 60 % 60, 10);//计算剩余的分钟数
        var ss = parseInt(ts / 1000 % 60, 10);//计算剩余的秒数
        mm = checkTime(mm);
        ss = checkTime(ss);
        if (ts > 0) {
            $(".carttime").html(mm + ":" + ss);
            $(".cart").animate({width: "160px"});
            setTimeout(function () {
                    privateFunction();
                },
                1000);
        } else {
            $(".carttime").html("");
            $(".cart").animate({width: "80px"});
        }
    }


    return {
        publicMethod: function () {
            return privateFunction();
        }
    };
}();

function checkTime(i) {
    if (i < 10) {
        i = "0" + i;
    }
    return i;
}
