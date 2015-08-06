
function Set_user_address(suffix){
	//设置用户地址列表信息
	var reqUrl = GLConfig.baseApiUrl + suffix;
	var callBack = function(data){
		//回调处理
		$.each(data,function(index,obj){
			obj.addr_class = obj.default==true?'active':'normal';
			var addr_dom = $('#addr-template').html().template(obj);
			$('.addr').append(addr_dom);
		});
	};
	// 调用接口
	$.ajax({ 
		type:'get', 
		url:reqUrl, 
		data:{}, 
		dataType:'json', 
		success:callBack 
	}); 
	
}

function Set_user_coupons(suffix){
	//设置用户可用优惠券列表
	var reqUrl = GLConfig.baseApiUrl + suffix;
	var callBack = function(data){
		//回调处理
		$.each(data,function(index,obj){
				var addr_dom = $('#coupon-template').html().template(obj);
				$('.coupons-list').append(addr_dom);
			}
		);
	};
	// 调用接口
	$.ajax({ 
		type:'get', 
		url:reqUrl, 
		data:{}, 
		dataType:'json', 
		success:callBack 
	}); 
	
}

function Set_user_orderinfo(suffix){
	//设置用户支付商品信息
	var reqUrl = GLConfig.baseApiUrl + suffix;
	var callBack = function(data){
		$('.cost .label1 span').html('<em>￥</em>' + data.total_fee);
		$('.cost .label2 span').html('<em>￥</em>' + data.post_fee);
		$('.buy .cou span').html('<em>￥</em>' + data.discount_fee);
		$('.buy .total span').html('<em>￥</em>' + data.total_payment);
		
		if (data.wallet_payable){
			$('.pay-type .pay-list').append('<li class="normal"><i id="wallet"></i>小鹿钱包</li>');
		}
		if (data.weixin_payable){
			$('.pay-type .pay-list').append('<li class="normal"><i id="wx_pub"></i>微信支付</li>');
		}
		if (data.alipay_payable){
			$('.pay-type .pay-list').append('<li class="normal"><i id="alipay_wap"></i>支付宝</li>');
		}
		$('.pay-type .pay-list li:first').removeClass('normal').addClass('active');
		
		var form_tempalte = $('#form-template').html().template(data);
		$('#item-list').html(form_tempalte);
	};
	// 调用接口
	$.ajax({ 
		type:'get', 
		url:reqUrl, 
		data:{}, 
		dataType:'json', 
		success:callBack 
	}); 
}

function Ctrl_sure_charge(pay_url){
	//确认支付
	if ($('.btn-buy').hasClass('charged')){return;}       
	var WALLET_PAY = 'wallet';	
    var CHARGE_URL  = GLConfig.baseApiUrl + pay_url;
	var channel     = $('.pay-type .pay-list li.active i').attr('id');
	if (isNone(channel)){
		drawToast('请选择正确的支付方式');
    	return
	}
    
    var addrid = $('.addr li.active i').attr('addrid');
    if (isNone(addrid)){
    	drawToast('请填写收货信息');
    	return
    }
    //获取表单参数
	var params = {};
	var form_array = $('#pay-form').serializeArray();
	$.map(form_array,function(n, i){
	        params[n['name']] = n['value'];
	});
	if(channel == WALLET_PAY && !confirm("确认使用小鹿钱包支付金额（￥"+params.payment+'元)吗？')){
		return 
	}
	params.addr_id = addrid;
	params.channel = channel;
	params.csrftoken = csrftoken;
	
    $('.btn-buy').addClass('charged');
    $('.btn-buy').addClass('pressed');

    var callback = function(data){
      
      if(isNone(data.errcode)){ 
      	if (data.channel == WALLET_PAY){//使用钱包支付
      		window.location.href = GLConfig.zhifucg_url;
      	}else{
          pingpp.createPayment(data, function(result, err) {
          	if (result == "success") {
		        window.location.href =  GLConfig.zhifucg_url;
		    } else if (result == "fail") {
		        window.location.href =  GLConfig.daizhifu_url;
		    } else if (result == "cancel") {
		        window.location.href =  GLConfig.daizhifu_url;
		    }
            
          });
        }
       }else{
       	 alert('err:' + data.errmsg);
       }
    }
    
	$.post(CHARGE_URL,params,callback,'json');
}

function update_total_price(){
	//更新订单价格显示
}

function plus_shop(id) {
    var num_id = $("#num_" + id);
    num_id.val(parseInt(num_id.val()) + 1);
    update_total_price();
}

function minus_shop(id) {
    var num_id = $("#num_" + id);
    num_id.val(parseInt(num_id.val()) - 1);
    update_total_price();
}



