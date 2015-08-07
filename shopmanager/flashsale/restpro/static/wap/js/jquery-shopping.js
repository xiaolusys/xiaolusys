/**
 * Created by yann on 15-7-29.
 */


(function ($) {
    $.extend($.fn, {
    	//监听购物车点击事件
        listencart: function (options) {
        	var self = this;
        	console.log('listercart');
        	var C = {
                init: function () {
                    $(self).data('click', true).on('click', this.doIflogin);
                },
                doIflogin:function(){
                	DoIfLogin({
			    		callback:function(){window.location='/pages/gouwuche.html';},
			    		redirecto:'/pages/gouwuche.html'
			    	});
                }
            };
        	C.init();
        },
        shoping: function (options) {
            var self = this,
                $shop = $('.cart'),
                $body = $('.J-shoping-body')
            var S = {
                init: function () {
                    $(self).data('click', true).on('click', this.addShoping);
                },
                addShoping: function (e) {
                    console.log('debug:',e);
                    e.stopPropagation();
                    //如果未选中商品尺寸,事件不执行
                    if ($('#js-goods-size li.active').length == 0){
                    	document.getElementById('js-goods-size').scrollIntoView(false);
                    	drawToast('请选择正确的商品尺寸');
                    	return;
                    };
                    var $target = $(e.target),
                        id = $target.attr('id'),
                        dis = $target.data('click'),
                        x = $target.offset().left + 30,
                        y = $target.offset().top + 10,
                        X = $shop.offset().left + $shop.width() / 2 - $target.width() / 2 + 10,
                        Y = $shop.offset().top;
                    console.log(dis);
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