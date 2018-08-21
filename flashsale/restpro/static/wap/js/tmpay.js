
function Set_user_address(suffix){
    //设置用户地址列表信息
    var reqUrl = GLConfig.baseApiUrl + suffix;
    var callBack = function(data){
        //回调处理
        if (data.length == 0){
            drawToast('请添加收货地址');
            return
        }
        var defaultAddr = data[0];
        defaultAddr.addr_class = defaultAddr.default==true?'active':'normal';
        var addr_dom = $('#addr-template').html().template(defaultAddr);
        $('.addr').append(addr_dom);
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
            $('.pay-type .pay-list').append('<li class="normal" name="select-pay"><i id="wallet"></i>妈妈钱包</li>');
        }
        if (data.weixin_payable){
            $('.pay-type .pay-list').append('<li class="normal" name="select-pay"><i id="wx_pub"></i>微信支付</li>');
        }
        if (data.alipay_payable){
            $('.pay-type .pay-list').append('<li class="normal" name="select-pay"><i id="alipay_wap"></i>支付宝</li>');
        }
        $('.pay-type .pay-list li:first').removeClass('normal').addClass('active');
        if (!isNone(data.sku)){
            var form_tempalte = $('#form-template').html().template(data);
            $('#item-list').html(form_tempalte);
        }
        if (!isNone(data.cart_list)){
            var item_template = $('#item-template').html();
            $.each(data.cart_list,function(index,cart){
                $('#item-list').append(item_template.template(cart));
            })
            var form_template = $('#form-template').html();
            $('#item-list').append(form_template.template(data));
        }
        console.log('debug coupon ticket:',data.coupon_ticket);
        if (!isNone(data.coupon_ticket)){
            var coupon_template = $('#coupon_c_valid').html();
            $('.coupons-list').append(coupon_template.template(data.coupon_ticket));
        }
        set_pro_num();
        var cart_ids = getUrlParam('cart_ids');
        if(cart_ids==null){//表示
            update_total_price();
        }
        if(data.coupon_message){// 如果优惠券的提示信息不是''，则提示优惠券信息　且不能提交当前页面
            drawToast(data.coupon_message);
        }
//        小能客服订单转化对接
//        var params = {
//            'profile':JSON.parse(getCookie(PROFILE_COOKIE_NAME) || '{}'),
//            'trade':data
//        }
//        loadNTalker(params,function(){});
    };
    // 调用接口
    $.ajax({ 
        type:'get', 
        url:reqUrl, 
        data:{}, 
        dataType:'json', 
        success:callBack ,
        error:function(err){
            var resp = JSON.parse(err.responseText);
            if (!isNone(resp.detail)){
                drawToast(resp.detail);
            }
        }
    }); 
}

var click_paybtn = click_paybtn || false;

function Ctrl_sure_charge(pay_url){
    //确认支付
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
    var couponid = $('.coupons li i').attr('couponid');
    $('input[name="buyer_message"]').val($('#id_buyer_message').val());
    //获取表单参数
    var params = {};
    var form_array = $('#pay-form').serializeArray();
    $.map(form_array,function(n, i){
        params[n['name']] = n['value'];
    });
    //防止重复点击
    if (click_paybtn == true){
        console.log('点击重复提交：'+new Date());
        return;
    }
    click_paybtn = true;
    if(channel == WALLET_PAY && !confirm("确认使用妈妈钱包支付金额（￥"+params.payment+'元)吗？')){
        click_paybtn = false;
        return;
    }
    params.addr_id = addrid;
    params.channel = channel;
    params.csrfmiddlewaretoken = csrftoken;
    params.mm_linkid = getUrlParam('mm_linkid');
    params.ufrom     = getUrlParam('ufrom');
    if(!isNone(couponid)){
        params.coupon_id = couponid;
    }
    var callBack = function(data){
        click_paybtn = false;
        var redirect_url = '/index.html';
        if (data.channel == WALLET_PAY){//使用钱包支付
          redirect_url = GLConfig.zhifucg_url+'?out_trade_no='+params['uuid'];
          window.location.href = adjustPageLink(redirect_url);
        }else{
          pingpp.createPayment(data, function(result, err) {
              if (result == "success") {
                redirect_url = GLConfig.zhifucg_url+'?out_trade_no='+params['uuid'];
            } else if (result == "fail") {
                redirect_url = GLConfig.daizhifu_url;
            } else if (result == "cancel") {
                redirect_url = GLConfig.daizhifu_url;
            }
            window.location.href = adjustPageLink(redirect_url);
          });
        }
    }
    // 调用接口
    $.ajax({ 
        type:'post', 
        url:CHARGE_URL, 
        data:params, 
        dataType:'json', 
        success:callBack,
        error:function(err){
            click_paybtn = false;
            console.log("err is here ", err);
            var resp = JSON.parse(err.responseText);
            if (!isNone(resp.detail)){
                drawToast(resp.detail);
            }else{
                drawToast('支付异常');
            }
        } 
    });
}

function Ctrl_order_charge(pay_url){
    //待支付订单确认支付
    var CHARGE_URL  = GLConfig.baseApiUrl + pay_url;
    var WALLET_PAY  = 'wallet';
    $('.btn-buy').addClass('pressed');
    var params = {};
    if (click_paybtn == true){
        return;
    }else{    
        click_paybtn = true;
    }
    var callBack = function(data){
        click_paybtn = false;
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
    }
    
    // 调用接口
    $.ajax({ 
        type:'post', 
        url:CHARGE_URL, 
        data:params, 
        dataType:'json', 
        success:callBack,
        error:function(err){
            click_paybtn = false;
            $('.btn-buy').removeClass('pressed');
            var resp = JSON.parse(err.responseText);
            if (!isNone(resp.detail)){
                drawToast(resp.detail);
            }else{
                drawToast('支付异常');
            }
        } 
    });
}

function update_total_price(){
    //更新订单价格显示
    var sku_price = parseFloat($('input[name="agent_price"]').val());
    var sku_num   = parseInt($('input[name="num"]').val());
    var discount_fee   = parseFloat($('input[name="discount_fee"]').val());
    var post_fee   = parseFloat($('input[name="post_fee"]').val());
    var total_fee = (sku_price * sku_num).toFixed(2);
    var total_payment = (total_fee + post_fee - discount_fee).toFixed(2);
    $('.cost .label1 span').html('<em>￥</em>' + total_fee);
    $('.buy .total span').html('¥ ' + total_payment);
    $('input[name="total_fee"]').val(total_fee);
    $('input[name="payment"]').val(total_payment);
}

function plus_shop(sku_id) {
    var sku_num = parseInt($("#num_" + sku_id).val());
    var params  = {'sku_id':sku_id, 'sku_num':sku_num + 1, 'csrfmiddlewaretoken':getCSRF()};
    var PLUS_URL = GLConfig.baseApiUrl + GLConfig.get_plus_skunum_url;
    var callBack = function(resp){
        $("#num_" + resp.sku_id).val(resp.sku_num);
        update_total_price();
    }
    // 调用接口
    $.ajax({ 
        type:'post', 
        url:PLUS_URL, 
        data:params, 
        dataType:'json', 
        success:callBack,
        error:function(err){
            var resp = JSON.parse(err.responseText);
            if (!isNone(resp.detail)){
                drawToast(resp.detail);
            }else{
                drawToast('添加订单数量异常');
            }
        } 
    });
    
}

function minus_shop(sku_id) {
    var sku_num = parseInt($("#num_" + sku_id).val());
    if (sku_num <= 1){return}
    $("#num_" + sku_id).val(sku_num - 1);
    update_total_price();
}


function messFocusCtrl(dom){
    $(dom).css('height','90px').css('width','510px');
}

function messBluCtrl(dom){
    $(dom).css('height','40px').css('width','510px');
}

