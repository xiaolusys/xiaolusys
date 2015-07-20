
function Create_order_dom(obj){
	function Order_dom(){
	/*
	<li>
    <div class="top clear">
      <div class="xiadan">下单时间：{{ created }}</div>
      <div class="shengyu">剩余时间：{{ remain_time }}</div>
    </div>
    <a href="./dd-detail.html?id={{ id }}" class="info clear">
      <div class="left"><img src="{{ order_pic }}" /></div>
      <div class="right">
        <p>订单编号：<span class="caaaaaa orderno">{{ tid }}</span></p>
        <p>订单状态：<span class="caaaaaa">{{ status_display }}</span></p>
        <p>订单金额：<span class="cf353a0"><em>¥</em>{{ payment }}</span></p>
      </div>
    </a>
    </li>
    */};
  
  return hereDoc(Order_dom).template(obj)
}

function Set_orders(suffix){
	//请求URL
	var requestUrl = GLConfig.baseApiUrl + suffix;
	
	//请求成功回调函数
	var requestCallBack = function(data){
		if (data.count != 'undifine' && data.count != null){
			$.each(data.results,
				function(index,order){
					var order_dom = Create_order_dom(order);
					$('.order_ul').append(order_dom);
				}
			);
		}
	};
	// 发送请求
	$.ajax({ 
		type:'get', 
		url:requestUrl, 
		data:{}, 
		dataType:'json', 
		success:requestCallBack 
	}); 
}

function Create_order_top_dom(obj){
	//创建订单基本信息DOM
	function Top_dom(){
	/*
    <ul class="u1">
      <li><label class="c5f5f5e">订单状态：</label><span class="caaaaaa">{{ status_display }}</span></li>
      <li><label class="c5f5f5e">订单编号：</label><span class="caaaaaa">{{ tid }}</span></li>
      <li><label class="c5f5f5e">订单时间：</label><span class="caaaaaa">{{ created }}</span></li>
      <li><label class="c5f5f5e">订单金额：</label><span class="cf353a0"><em>¥</em>{{ payment }}</span></li>
    </ul>
    <a href="#" class="btn-quxiao">取消订单</a>
	*/};
	return hereDoc(Top_dom).template(obj);
}

function Create_detail_dom(obj){
	//创建订单基本信息DOM
	function Detail_topdom(){
	/*
	   <div class="goods clear">
	      <div class="fl goods-img">
	        <img src="{{ pic_path }}">
	      </div> 
	      <div class="fr goods-info">
	        <p>{{ title }}</p>
	        <p>
	          <span class="size">尺码：{{ sku_name }}</span> 
	          <span class="count">数量：{{ num }}</span>
	        </p>
	        <p class="price">单价：<span class="gprice"><em>¥</em>{{ payment }}</span></p>
	      </div> 
	    </div> 
	*/};
	return hereDoc(Detail_topdom).template(obj);
}
 
function Create_detail_shouhuo_dom(obj){
	//创建订单收货信息DOM
	function Shouhuo_dom(){
	/*
    <div class="info">
      <p class="clear">
        <span class="label">收货人：</span>
        <span class="value">{{ obj.receiver_name }}</span>
      </p>
      <p class="clear">
        <span class="label">手机号码：</span>
        <span class="value">{{ obj.receiver_mobile }}</span>
      </p>
      <p class="clear">
        <span class="label">收货地址：</span>
        <span class="value">{{ obj.receiver_state }} - {{ obj.receiver_city }} - {{ obj.receiver_district }} - {{ receiver_address }}</span>
      </p>  
    </div>
	*/};
	return hereDoc(Shouhuo_dom).template(obj);
}

function Create_detail_feiyong_dom(obj){
	//创建订单费用信息DOM
	function Feiyong_dom(){
	/*
    <div class="info">
      <p class="clear">
        <span class="label">商品总金额：</span>
        <span class="value"><em>¥</em> {{ total_fee }}</span>
      </p>
      <p class="clear">
        <span class="label">运费：</span>
        <span class="value"><em>¥</em> {{ post_fee }}</span>
      </p>
      <p class="clear">
        <span class="label">优惠金额：</span>
        <span class="value"><em>¥</em> -{{ discount_fee }}</span>
      </p> 
      <p class="clear">
        <span class="label">应付金额：</span>
        <span class="value total"><em>¥</em> {{ payment }}</span>
      </p>  
    </div>
	*/};
	return hereDoc(Feiyong_dom).template(obj);
}


function Set_order_detail(suffix){
	//请求URL
	var requestUrl = GLConfig.baseApiUrl + suffix;
	
	//请求成功回调函数
	var requestCallBack = function(data){
		if (data.id != 'undifine' && data.id != null){
			//设置订单基本信息
			var top_dom = Create_order_top_dom(data);
			$('.basic .panel-top').append(top_dom);
			//设置订单收货信息
			var shouhuo_dom = Create_detail_shouhuo_dom(data);
			$('.shouhuo .panel-bottom').append(shouhuo_dom);
			//设置订单费用信息
			var feiyong_dom = Create_detail_feiyong_dom(data);
			$('.feiyong .panel-bottom').append(feiyong_dom);
			//设置订单商品明细
			$.each(data.orders,
				function(index,order){
					var detail_dom = Create_detail_dom(order);		
					$('.basic .panel-bottom').append(detail_dom);			
				}
			);
		}
	};
	// 发送请求
	$.ajax({ 
		type:'get', 
		url:requestUrl, 
		data:{}, 
		dataType:'json', 
		success:requestCallBack 
	}); 
}



