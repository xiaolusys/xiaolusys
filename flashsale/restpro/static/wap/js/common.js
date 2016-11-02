/**
 *@author: imeron
 *@date: 2015-07-22
 */
var PROFILE_COOKIE_NAME = 'Xl_profile';
var EXPIRED_DAYS = 1;
 
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
    return typeof(value) == 'undifined' || value == null || value == '';
}

function getLinkParam(url,name){
    var reg = new RegExp('[\\?&]' + name + '=([^&#]*)');
    var r = url.substr(1).match(reg);
    if (r != null) return unescape(r[1]);
    return null;
}

function getUrlParam(name) {
    var local_link = window.location.href;
    return getLinkParam(local_link,name);
}

//定义多行字符串函数实现
function hereDoc(f) {
    return f.toString().replace(/^[^\/]+\/\*!?\s?/, '').replace(/\*\/[^\/]+$/, '');
}

//全局配置
var GLConfig = {
	user_profile:null,
	baseApiUrl:'/rest/v1', //API接口调用前缀
	order_expired_in:20 * 60,//expired time
	login_url:'/pages/denglu.html',//登录URL
	zhifucg_url:'/pages/zhifucg.html',//支付成功跳转URL
	daizhifu_url:'daizhifu-dd.html',//待支付订单页面
	poster_today:'/posters/today.json',  //获取今日特卖海报
	poster_previous:'/posters/previous.json',  //获取昨日特卖海报
	products_today:'/products/promote_today.json',  //获取昨日特卖推荐列表
	products_today_paging:'/products/promote_today_paging.json',  //获取昨日特卖推荐分页列表
	promote_previous_paging:'/products/promote_previous_paging.json',  //获取昨日特卖推荐分页列表
	products_previous:'/products/promote_previous.json',  //获取昨日特卖推荐列表
	get_childlist_url:'/products/childlist.json', //获取潮流童装商品列表
	get_ladylist_url:'/products/ladylist.json', //获取时尚女装商品列表
	get_modellist_url:'/products/modellist/{{model_id}}.json', //获取同款商品列表
	get_modellist_preview_url:'/products/preview_modellist/{{model_id}}.json', //获取同款商品列表(同款预览页面)
	get_product_detail_url:'/products/{{product_id}}/details.json', //获取商品明细
    verify_product:"/products/{{id}}/verify_product",//审核产品
	get_trade_all_url:'/trades.json', //获取用户特卖订单
	get_wxorder_all_url:'/wxorders.json', //获取用户历史订单
	get_trade_waitpay_url:'/trades/waitpay.json', //获取用户待付款订单
	get_trade_waitsend_url:'/trades/waitsend.json', //获取用户待发货订单
	get_trade_details_url:'/trades/{{trade_id}}/details.json', //获取订单明细
    get_order_detail_url:'/trades/{{ tid }}/orders/{{ oid　}}',//获取单个SaleOrder明细
    get_wxorder_detail_url:'/wxorders/{{ trade_id }}.json',//获取单个Wxorder明细
	get_trade_charge_url:'/trades/shoppingcart_create.json', //购物车结算订单接口
	get_buynow_url:'/trades/buynow_create.json', //立即购物订单创建接口
	waitpay_charge:'/trades/{{trade_id}}/charge.json', //待支付订单结算接口
	get_cart_url:'/carts.json', //获取购物车详细
	get_cart_payinfo_url:'/carts/carts_payinfo.json', //根据购物车id列表获取支付明细
	get_now_payinfo_url:'/carts/now_payinfo.json', //根据购物车id列表获取支付明细
	get_num_cart:'/carts/show_carts_num?format=json', //获取购物车数量
	get_plus_skunum_url:'/carts/sku_num_enough.json', //添加订单数量接口
	get_all_address:'/address.json',//获取个人用户地址列表
	get_user_address:'/address.json',//获取个人用户地址列表
	change_default:'/address/change_default/?format=json',//更改默认地址
	province_list:'/districts/province_list?format=json',//省份列表
	city_list:'/districts/city_list?format=json',//城市列表
	country_list:'/districts/country_list?format=json',//区/县列表
	create_address:'/address/create_address?format=json',//创建新的收货地址
	get_user_profile:'/users/profile.json',//得到用户信息
	get_user_point:'/integral.json',//得到用户积分
	delete_detail_trade:'/trades/{{trade_id}}',//用户取消订单
    confirm_sign_order:'/order/{{order_id}}/confirm_sign',//用户确认签收
    usercoupons:"/usercoupons",//2015-09-04　重构后的优惠券接口
    past_usercoupons:"/usercoupons/list_past_coupon",//2015-09-04　重构后的优惠券接口 过期的优惠券
    coupon_tpls:"/cpntmpl",//  优惠券模板接口
    choose_coupon:"/usercoupons/{{ coupon_id }}/choose_coupon",//选择优惠券（校验优惠券）
	user_logout:'/users/customer_logout',//用户注销
	user_islogin:'/users/islogin.json',//用户是否登录
    refunds:'/refunds',//退款
    refunds_by_order_id:"/refunds/{{order_id}}/get_by_order_id",
    sale_product: "/saleproduct",   //获取特卖选品列表
    api_share_page:'/share/today.json',//分享店铺主页
    api_share_model:'/share/model.json',//分享店铺主页
    api_share_product:'/share/product.json',//分享商品详情页
    change_hot_val: "/saleproduct/{{ id }}/change_hot_val",   //添加热度值
    hot_product: "/hotproduct",   //获取特卖选品列表
    change_hot_pro_hot_val: "/hotproduct/{{ id }}/change_hot_val",   //添加热度值
    app_download: "/download/get_app_download_link",   //添加热度值
    mama_shop: "/products/get_mama_shop", // 获取代理用户店铺基础信息
    activitys_url: "/activitys",// 活动页面h5入口
    agency_invitation_res:'/rest/v2/referal',//代理邀请结果(我的邀请页面)
    get_mama_fortune:'/rest/v2/fortune'//代理财富

};

var s;
var ua = navigator.userAgent.toLowerCase();
(s = ua.match(/msie ([\d.]+)/)) ? GLConfig.ie = s[1] :
(s = ua.match(/firefox\/([\d.]+)/)) ? GLConfig.firefox = s[1] :
(s = ua.match(/chrome\/([\d.]+)/)) ? GLConfig.chrome = s[1] :
(s = ua.match(/opera.([\d.]+)/)) ? GLConfig.opera = s[1] :
(s = ua.match(/version\/([\d.]+).*safari/)) ? GLConfig.safari = s[1] : 0;
(s = ua.match(/micromessenger\/([\d.]+).*/)) ? GLConfig.weixin = s[1] : GLConfig.weixin = 0;

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
function setCookie(c_name,value,expiredays){
	var exdate=new Date();
	exdate.setDate(exdate.getDate()+expiredays);
	document.cookie=c_name+ "=" +encodeURIComponent(value)+
	((expiredays==null) ? "" : "; expires="+exdate.toGMTString());
}
function delCookie(name){
    //删除cookie
    var exp = new Date();
    exp.setTime(exp.getTime() - 1);
    var cval=getCookie(name);
    if(cval!=null) document.cookie= name + "="+cval+";expires="+exp.toGMTString();
}
function getCSRF(){
	return getCookie('csrftoken');
}
var csrftoken = getCSRF();

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
    intervalCounter = setInterval("hideToast()", 2000);
}

function DoIfLogin(cfg){
	var profile = getCookie(PROFILE_COOKIE_NAME);
	if (!isNone(profile)){
		cfg.callback();
		return;
	};
	function cookieProfile(data){
		data.nick_alias = data.nick==''?'无名':data.nick;
		var profile_str = JSON.stringify(data);
		setCookie(PROFILE_COOKIE_NAME,profile_str,EXPIRED_DAYS);
		cfg.callback();
	};
	$.ajax({
        type: 'get',
        url: GLConfig.baseApiUrl + GLConfig.get_user_profile,
        data: "",
        success: cookieProfile,
        error: function (data) {
            if (data.status == 403) {
                window.location = GLConfig.login_url+'?next='+encodeURIComponent(adjustPageLink(cfg.redirecto));
            }
        }
    });
}

function btnPresse(){
	$(this).addClass('pressed');
}

function btnUnpresse(){
	$(this).removeClass('pressed');
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
    var count = 0;

    function privateFunction() {
        var ts = remain_date - (new Date());//计算剩余的毫秒数
        var mm = parseInt(ts / 1000 / 60 % 60, 10);//计算剩余的分钟数
        var ss = parseInt(ts / 1000 % 60, 10);//计算剩余的秒数
        mm = checkTime(mm);
        ss = checkTime(ss);
        if (count == 1) {
            if (ts > 0) {
                if (ts > 299400 && ts < 300600) {
                    swal({
                            title: "",
                            text: "亲,5分钟后购物车的商品将被清空，去购物车结算吗？",
                            type: "",
                            showCancelButton: true,
                            imageUrl: "http://img.xiaolumeimei.com/logo.png",
                            confirmButtonColor: '#DD6B55',
                            confirmButtonText: '去购物车',
                            cancelButtonText: '取消'
                        },
                        function () {
                            //发送请求
                            window.location = "/pages/gouwuche.html";
                        });
                }
                $(".carttime").html(mm + ":" + ss);
                $(".cart").animate({width: "170px"});
                setTimeout(function () {
                        privateFunction();
                    },
                    1000);


            } else {
                $(".carttime").html("");
                $(".cart").animate({width: "80px"});
            }
        } else {
            count = 1;
        }
    }
    return {
        publicMethod: function () {
            count++;
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

function loadBaiduStat(){
	var _hmt = _hmt || [];
	(function() {
	  var hm = document.createElement("script");
	  hm.src = "//hm.baidu.com/hm.js?f8a445bf4aa2309eb173c6ad194dd6e7";
	  var s = document.getElementsByTagName("script")[0]; 
	  s.parentNode.insertBefore(hm, s);
	})();
}

function makePicUlr(pic_url,params){
	var url_params = '&imageMogr2/';
	if (!isNone(params.size)){
		url_params += 'thumbnail/{{size}}/';
	}
	if (!isNone(params.format)){
		url_params += 'format/{{format}}/';
	}
	if (!isNone(params.quality)){
		url_params += 'quality/{{quality}}/';
	}
	url_params = url_params.template(params);
	if (pic_url.indexOf('?')>0){
		return pic_url + url_params;
	}
	return pic_url + '?' + url_params;
}

function parseUrlParams(link){
    var vars = {}, hash;
    if (link.indexOf('?') < 0)return vars;
    var hashes = link.slice(link.indexOf('?') + 1).split('&');
    for (var i = 0; i < hashes.length; i++) {
        hash = hashes[i].split('=');
        vars[hash[0]] = hash[1];
    }
    return vars
}

function makeLinkUrl(link,params){
    if (isNone(link) || /^(javascript|#)/.test(link)){
        console.log('invalid link:',link);
        return link
    }
    var vars = parseUrlParams(link);
    for (var p in params){
        if (params[p]==null)continue;
        vars[p] = params[p];
    }
    if (link.indexOf('?') < 0){
        return link + '?' + $.param(vars);
    }
    return link.slice(0,link.indexOf('?'))+'?'+$.param(vars)
}

function adjustPageLink(link){
    var params  = {'mm_linkid':getUrlParam('mm_linkid'),'ufrom':getUrlParam('ufrom')};
    return makeLinkUrl(link,params);
}

//加载小能客服插件
function loadNTalker(params,callback){
	var NTKF_PARAM = NTKF_PARAM || null;
	console.log('debug NTKF_PARAM:',NTKF_PARAM);
	if (!isNone(NTKF_PARAM)){
		callback();
		return
	};
	var ntkf_template = document.getElementById('ntkf_template').innerHTML;
	var ntkf_dom	  = document.createElement("script");
	ntkf_dom.type 	  = "text/javascript";
	ntkf_dom.innerHTML = ntkf_template.template(params);
	
	var ntkf_sc = document.createElement("script");
	ntkf_sc.type 	= "text/javascript";
	ntkf_sc.src 	= "http://dl.ntalker.com/js/xn6/ntkfstat.js?siteid=kf_9645";
	ntkf_sc.charset = 'utf-8';
	ntkf_sc.onload  = callback;
	// IE 6 & 7
	ntkf_sc.onreadystatechange = function() {
		if (this.readyState == 'loaded' || this.readyState == 'complete') {
			callback();
		}
	}
	console.log('debug ntkf dom:',ntkf_dom,ntkf_sc);
	document.body.appendChild(ntkf_dom);
	document.body.appendChild(ntkf_sc);
}

//设置初始页面VIEWPORT
(function () {
    var oViewport = document.getElementById('viewport');
    var phoneWidth = parseInt(window.screen.width);
    var phoneScale = phoneWidth / 640;
    var ua = navigator.userAgent.toLowerCase();
    if (/android (\d+\.\d+)/.test(ua)) {
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
        //window.event.cacenlBubble=false;
        if(document.addEventListener){
	        if (window.navigator.standalone) jQuery.ajaxSetup({isLocal:true});
	        document.body.addEventListener('click',function(e){
	            var target = e.target || e.srcElement;
	            var parentTarget = target.parentNode;
	            if (target.nodeName.toLowerCase() === 'a' && !isNone(target.href)) {
			        target.href = adjustPageLink(target.href);
			    }else if(parentTarget.nodeName.toLowerCase() === 'a' && !isNone(parentTarget.href)){
			        parentTarget.href = adjustPageLink(parentTarget.href);
			    }
	        },false);
	    }
        //加载百度统计插件
        loadBaiduStat();
    }
    window.onbeforeunload = function(event){
        //to handle unload page,cannot replace location;
    }
})();

