/**
 * Created by yann on 15-7-29.
 */

(function ($) {
    $.extend($.fn, {
    	//监听购物车点击事件
        listencart: function (options) {
        	var self = this;
        	var C = {
                init: function () {
                    $(self).data('click', true).on('click', this.doIflogin);
                },
                doIflogin:function(){
                	DoIfLogin({
			    		callback:function(){window.location=adjustPageLink('/pages/gouwuche.html');},
			    		redirecto:adjustPageLink('/pages/gouwuche.html')
			    	});
                }
            };
        	C.init();
        },
        shoping: function (options) {
            var self = this,
                $shop = $('.cart'),
                $body = $('.J-shoping-body'),
                $event = null;
            var S = {
                init: function () {
                    $(self).data('click', true).on('click', this.doIflogin);
                },
                doIflogin:function(e){
                	e.stopPropagation();
                	$event = e;
                	DoIfLogin({
			    		callback:function(){ 
			    			S.addCartItem();
				    	},
				    	redirecto:window.location.href
				    });
                }, 
                addCartItem: function() {
                	var item_id = $("#product_id").html();
				    var sku = $("#js-goods-size li.active");
				    //如果未选中商品尺寸,事件不执行
                    if (sku.length == 0){
                    	document.getElementById('js-goods-size').scrollIntoView(false);
                    	drawToast('请选择商品尺寸');
                    	return;
                    };
				    var sku_id = sku.eq(0).attr("sku_id");
				    var num = 1;
				    var requestUrl = GLConfig.baseApiUrl + GLConfig.get_cart_url;
				    var requestCallBack = function (res) {
				    	S.addShoping();
				        Set_shopcarts_num();
				    };
				    // 发送请求
				    $.ajax({
				        type: 'post',
				        url: requestUrl,
				        data: {"num": num, "item_id": item_id, "sku_id": sku_id, "csrfmiddlewaretoken": csrftoken},
				        beforeSend: function () {
				
				        },
				        success: requestCallBack,
				        error: function (data) {
				            if(data.status >= 300){
				            	var errmsg = $.parseJSON(data.responseText).detail;
				            	drawToast(errmsg);
				                if(errmsg == "商品库存不足"){
				                    setTimeout(reload,1000)
				                }
				            }
				        }
				    });
                },
                addShoping: function () {
                	e = $event;
                    console.log('debug:',e);
                    var $target = $(e.target),
                        id = $target.attr('id'),
                        dis = $target.data('click'),
                        x = $target.offset().left + 30,
                        y = $target.offset().top + 10,
                        X = $shop.offset().left + $shop.width() / 2 - $target.width() / 2 + 10,
                        Y = $shop.offset().top;
                    if (dis) {
                        if ($('#floatOrder').length <= 0) {
                        	var cart_image_url =  $('.swiper-slide img').first().attr('src');
                            $('body').append('<div id="floatOrder"><img src="'+cart_image_url+'" width="25" height="25" /></div>');
                        }
                        var $obj = $('#floatOrder');
                        console.log(X);
                        if (!$obj.is(':animated')) {
                            $obj.css({'left': x, 'top': y}).animate({'left': X + 70, 'top': Y - 40}, 500, function () {
                                $obj.stop(false, false).animate({'top': Y - 20, 'opacity': 0}, 500, function () {
                                    $obj.fadeOut(300, function () {
                                        $obj.remove();
                                        //$target.data('click', false).addClass('dis-click');
                                    });
                                });
                            });
                        }

                    }

                }
            };
            S.init();
        }
    });
})(jQuery);