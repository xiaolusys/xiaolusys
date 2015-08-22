/**
 *@author: imeron
 *@date: 2015-07-22 
 */
var timestamp = Date.parse(new Date());
var wait = 60;
function time(btn) {
    if (wait == 0) {
        btn.click(get_code);
        btn.text("获取验证码");
        wait = 60;
    } else {
        btn.unbind("click")
        btn.text(wait + "秒后重新获取");
        wait--;
        setTimeout(function () {
                time(btn);
            },
            1000)
    }
}

var today = new Date();
function today_timer() {
    /*
     * 首页(今日)倒计时
     * auther:yann
     * date:2015/6/8
     */
    var ts = (new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1, 14, 0, 0)) - (new Date());//计算剩余的毫秒数
    var dd = parseInt(ts / 1000 / 60 / 60 / 24, 10);//计算剩余的天数
    var hh = parseInt(ts / 1000 / 60 / 60 % 24, 10);//计算剩余的小时数
    var mm = parseInt(ts / 1000 / 60 % 60, 10);//计算剩余的分钟数
    var ss = parseInt(ts / 1000 % 60, 10);//计算剩余的秒数
    dd = checkTime(dd);
    hh = checkTime(hh);
    mm = checkTime(mm);
    ss = checkTime(ss);
    console.log(dd, hh, mm, ss);
    if (ts > 100800000 && ts < 136800000) {
        $(".poster_timer.tm2").text("敬请期待");
    } else if (ts < 100800000 && ts >= 86400000) {
        $(".poster_timer.tm2").text("剩余" + dd + "天" + hh + "时" + mm + "分" + ss + "秒");
        setTimeout(function () {
                today_timer();
            },
            1000);
    } else if (ts < 86400000) {
        $(".poster_timer.tm2").text("剩余" + hh + "时" + mm + "分" + ss + "秒");
        setTimeout(function () {
                today_timer();
            },
            1000);
    }

}

function yesterday_timer() {
    /*
     * 昨日特卖倒计时
     * auther:yann
     * date:2015/6/8
     */
    var ts = (new Date(today.getFullYear(), today.getMonth(), today.getDate(), 14, 0, 0)) - (new Date());//计算剩余的毫秒数
    var dd = parseInt(ts / 1000 / 60 / 60 / 24, 10);//计算剩余的天数
    var hh = parseInt(ts / 1000 / 60 / 60 % 24, 10);//计算剩余的小时数
    var mm = parseInt(ts / 1000 / 60 % 60, 10);//计算剩余的分钟数
    var ss = parseInt(ts / 1000 % 60, 10);//计算剩余的秒数
    dd = checkTime(dd);
    hh = checkTime(hh);
    mm = checkTime(mm);
    ss = checkTime(ss);
    console.log(dd, hh, mm, ss);
    if (ts > 0) {
        $(".poster_timer.tm2").text(hh + "时" + mm + "分" + ss + "秒");
        setTimeout(function () {
                yesterday_timer();
            },
            1000);
    } else {
        $(".poster_timer.tm2").text("敬请期待明日上新");
    }
}
function tm_timer_today() {
    /*
     * 今天海报特卖倒计时
     * auther:yann
     * date:2015/20/8
     */
    var ts = (new Date(2015, 7, 23, 14, 0, 0)) - (new Date());//计算剩余的毫秒数
    var dd = parseInt(ts / 1000 / 60 / 60 / 24, 10);//计算剩余的天数
    var hh = parseInt(ts / 1000 / 60 / 60 % 24, 10);//计算剩余的小时数
    var mm = parseInt(ts / 1000 / 60 % 60, 10);//计算剩余的分钟数
    var ss = parseInt(ts / 1000 % 60, 10);//计算剩余的秒数
    dd = checkTime(dd);
    hh = checkTime(hh);
    mm = checkTime(mm);
    ss = checkTime(ss);
    console.log(dd, hh, mm, ss);
    if (ts >= 86400000) {
        $(".poster_timer.tm1").text("剩余" + dd + "天" + hh + "时" + mm + "分" + ss + "秒");
        setTimeout(function () {
                tm_timer_today();
            },
            1000);
    } else if (ts < 86400000 && ts > 0) {
        $(".poster_timer.tm1").text("剩余" + hh + "时" + mm + "分" + ss + "秒");
        setTimeout(function () {
                tm_timer_today();
            },
            1000);
    } else {
        $(".poster_timer.tm1").text("敬请期待下次活动");
    }
}
function tm_timer() {
    /*
     * 昨日海报特卖倒计时
     * auther:yann
     * date:2015/20/8
     */
    var ts = (new Date(2015, 7, 24, 14, 0, 0)) - (new Date());//计算剩余的毫秒数
    var dd = parseInt(ts / 1000 / 60 / 60 / 24, 10);//计算剩余的天数
    var hh = parseInt(ts / 1000 / 60 / 60 % 24, 10);//计算剩余的小时数
    var mm = parseInt(ts / 1000 / 60 % 60, 10);//计算剩余的分钟数
    var ss = parseInt(ts / 1000 % 60, 10);//计算剩余的秒数
    dd = checkTime(dd);
    hh = checkTime(hh);
    mm = checkTime(mm);
    ss = checkTime(ss);
    console.log(dd, hh, mm, ss);
    if (ts >= 86400000) {
        $(".poster_timer.tm1").text("剩余" + dd + "天" + hh + "时" + mm + "分" + ss + "秒");
        setTimeout(function () {
                tm_timer();
            },
            1000);
    } else if (ts < 86400000 && ts > 0) {
        $(".poster_timer.tm1").text("剩余" + hh + "时" + mm + "分" + ss + "秒");
        setTimeout(function () {
                tm_timer();
            },
            1000);
    } else {
        $(".poster_timer.tm1").text("敬请期待下次");
    }
}
function checkTime(i) {
    if (i < 10) {
        i = "0" + i;
    }
    return i;
}

function Set_posters(suffix){
	//获取海报
	var posterUrl = GLConfig.baseApiUrl + '/posters/'+ suffix +'.json';
	
	var posterCallBack = function(data){
		if (!isNone(data.wem_posters)){
			//设置女装海报链接及图片
			$.each(data.wem_posters,
				function(index,poster){
					$('.poster .nvzhuang').attr('href',poster.item_link);
					$('.poster .nvzhuang img').attr('src',poster.pic_link);
					if (poster.subject === 'undifine' || poster.subject === null ){
						return
					}
					$('.poster .nvzhuang .subject').html('<span class="tips">'+poster.subject[0]+'</span>'+poster.subject[1]);
				}
			);
		}
		if (!isNone(data.chd_posters)){
			//设置童装海报链接及图片
			$.each(data.chd_posters,
				function(index,poster){
					$('.poster .chaotong').attr('href',poster.item_link);
					$('.poster .chaotong img').attr('src',poster.pic_link);
					if (poster.subject === 'undifine' || poster.subject === null ){
						return
					}
					$('.poster .chaotong .subject').html('<span class="tips">'+poster.subject[0]+'</span>'+poster.subject[1]);
				}
			);
		}
	};
	// 请求海报数据
	$.ajax({ 
		type:'get', 
		url:posterUrl, 
		data:{}, 
		dataType:'json', 
		success:posterCallBack 
	}); 
}

function Create_item_dom(p_obj,close_model){
	
	//创建商品DOM
	function Item_dom(){
	/* 
	<li>
      <a href="pages/shangpinxq.html?id={{ id }}">
        <img src="{{ pic_path }}?imageMogr2/thumbnail/289x289">
        <p class="gname">{{ name }}</p>
        <p class="gprice">
          <span class="nprice"><em>¥</em> {{ agent_price }} </span>
          <s class="oprice"><em>¥</em> {{ std_sale_price }}</s>
        </p>{{ saleout_dom }}
      </a>
    </li>
    */
	};
	
	//创建商品款式DOM
	function Model_dom(){
	/* 
	<li>
      <a href="tongkuan.html?id={{ product_model.id }}">
        <img src="{{ product_model.head_imgs }}?imageMogr2/thumbnail/289x289">
        <p class="gname">{{ product_model.name }}</p>
        <p class="gprice">
          <span class="nprice"><em>¥</em> {{ agent_price }} </span>
          <s class="oprice"><em>¥</em> {{ std_sale_price }}</s>
        </p>{{ saleout_dom }}
      </a>
    </li>
    */
	};

    p_obj.saleout_dom = '';
    var today = new Date().Format("yyyy-MM-dd");

    //如果没有close model,并且model_product存在
    if (!close_model && !isNone(p_obj.product_model)) {
        if (!p_obj.is_saleopen) {
            if (p_obj.sale_time == today) {
                p_obj.saleout_dom = '<div class="mask"></div><div class="text">即将开售</div>';
            } else {
                p_obj.saleout_dom = '<div class="mask"></div><div class="text">已过期</div>';
            }
        }
        p_obj.product_model.head_imgs = p_obj.product_model.head_imgs[0]
        return hereDoc(Model_dom).template(p_obj);
    }

    //上架判断
    if (!p_obj.is_saleopen) {
        if (p_obj.sale_time == today) {
            p_obj.saleout_dom = '<div class="mask"></div><div class="text">即将开售</div>';
        } else {
            p_obj.saleout_dom = '<div class="mask"></div><div class="text">已过期</div>';
        }
    } else if (p_obj.is_saleout) {
        p_obj.saleout_dom = '<div class="mask"></div><div class="text">抢光了</div>';
    }
	return hereDoc(Item_dom).template(p_obj);
}

function Set_promotes_product(suffix){
	//获取今日推荐商品
	var promoteUrl = GLConfig.baseApiUrl + '/products/promote_'+ suffix +'.json';
	
	var promoteCallBack = function(data){
        $("#loading").hide();
		if (!isNone(data.female_list)){
			
			$('.glist .nvzhuang').empty();
			//设置女装推荐链接及图片
			$.each(data.female_list,
				function(index,p_obj){
					var item_dom = Create_item_dom(p_obj);
					$('.glist .nvzhuang').append(item_dom);
				}
			);
		}
		
		if (!isNone(data.child_list)){
			
			$('.glist .chaotong').empty();
			//设置童装推荐链接及图片
			$.each(data.child_list,
				function(index,p_obj){
					var item_dom = Create_item_dom(p_obj);
					$('.glist .chaotong').append(item_dom);
				}
			);
		}
	};
	// 请求推荐数据
	$.ajax({ 
		type:'get', 
		url:promoteUrl, 
		data:{}, 
		dataType:'json',
        beforeSend: function () {
            $("#loading").show();
        },
		success:promoteCallBack 
	}); 
	
}

function Set_category_product(suffix){
	//获取潮流童装商品
	var promoteUrl = GLConfig.baseApiUrl + suffix;
	
	var promoteCallBack = function(data){
		if (!isNone(data.results)){
            $("#loading").hide();
			//设置女装推荐链接及图片
			$.each(data.results,
				function(index,p_obj){
					var item_dom = Create_item_dom(p_obj,false);
					$('.glist').append(item_dom);
				}
			);
		}
	};
	// 请求推荐数据
	$.ajax({ 
		type:'get', 
		url:promoteUrl, 
		data:{}, 
		dataType:'json',
        beforeSend: function () {
            $("#loading").show();
        },
		success:promoteCallBack 
	}); 
	
}

function Set_model_product(suffix){
	//获取同款式商品列表
	var promoteUrl = GLConfig.baseApiUrl + suffix;
	
	var promoteCallBack = function(data){
        $("#loading").hide();
		//设置女装推荐链接及图片

		$.each(data,
			function(index,p_obj){
				var item_dom = Create_item_dom(p_obj,true);
				$('.glist').append(item_dom);
			}
		);
        if(data && data.length > 0 && data[0].sale_time){
            var shelf_time = new Date(data[0].sale_time);
            product_timer(shelf_time);
        }
	};
	// 请求推荐数据
	$.ajax({ 
		type:'get', 
		url:promoteUrl, 
		data:{}, 
		dataType:'json',
        beforeSend: function () {
            $("#loading").show();
        },
		success:promoteCallBack 
	}); 
	
}

function product_timer(shelf_time) {
    /*
     * 商品倒计时
     * auther:yann
     * date:2015/15/8
     */
    var ts = (new Date(shelf_time.getFullYear(), shelf_time.getMonth(), shelf_time.getDate() + 1, 14, 0, 0)) - (new Date());//计算剩余的毫秒数

    var dd = parseInt(ts / 1000 / 60 / 60 / 24, 10);//计算剩余的天数
    var hh = parseInt(ts / 1000 / 60 / 60 % 24, 10);//计算剩余的小时数
    var mm = parseInt(ts / 1000 / 60 % 60, 10);//计算剩余的分钟数
    var ss = parseInt(ts / 1000 % 60, 10);//计算剩余的秒数
    dd = checkTime(dd);
    hh = checkTime(hh);
    mm = checkTime(mm);
    ss = checkTime(ss);

    if (ts > 100800000 && ts < 136800000) {
        $(".top p").text("敬请期待");
    } else if (ts < 100800000 && ts >= 86400000) {
        $(".top p").text("剩余" + dd + "天" + hh + "时" + mm + "分");
        setTimeout(function () {
                product_timer(shelf_time);
            },
            2000);
    } else if (ts < 86400000 && ts > 0) {
        $(".top p").text("剩余" + hh + "时" + mm + "分");
        setTimeout(function () {
                product_timer(shelf_time);
            },
            2000);
    } else if (ts < 0) {
        $(".top p").text("已下架");
    }

}

    /*
     * 时间格式化
     * auther:yann
     * date:2015/22/8
     */
Date.prototype.Format = function (fmt) {
    var o = {
        "M+": this.getMonth() + 1, //月份
        "d+": this.getDate(), //日
        "h+": this.getHours(), //小时
        "m+": this.getMinutes(), //分
        "s+": this.getSeconds(), //秒
        "q+": Math.floor((this.getMonth() + 3) / 3), //季度
        "S": this.getMilliseconds() //毫秒
    };
    if (/(y+)/.test(fmt)) fmt = fmt.replace(RegExp.$1, (this.getFullYear() + "").substr(4 - RegExp.$1.length));
    for (var k in o)
    if (new RegExp("(" + k + ")").test(fmt)) fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]) : (("00" + o[k]).substr(("" + o[k]).length)));
    return fmt;
}