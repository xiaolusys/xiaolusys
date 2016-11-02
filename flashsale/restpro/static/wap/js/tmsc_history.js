function get_history_carts(suffix) {
    /*
     * 获取历史购物车内容
     * auther:yann
     * date:2015/29/8
     */
    //请求URL
    var requestUrl = GLConfig.baseApiUrl + "/carts/show_carts_history.json";

    //请求成功回调函数
    var requestCallBack = function (data) {

        $("#loading").hide();
        $('.cart-list').empty();
        if (data && data.length > 0) {
            $('body').append(template('logo_template', {"show":false}));
            $.each(data,
                function (index, product) {
                    var html = template('item_template', product);
                    $('.cart-list').append(html);
                    if(product.is_sale_out){
                        $(".cart-list #item_"+product.id+" .gprice").eq(0).css("color","rgba(0,0,0,0.6)")
                        $(".cart-list #item_"+product.id+" .history-btn").eq(0).css("color","rgba(0,0,0,0.6)")
                        $(".cart-list #item_"+product.id+" .historydiv").eq(0).css("border","1px solid rgba(0,0,0,0.6)")
                    }
                }
            );
        } else {
            $('body').append(template('logo_template', {"show":true}));
        }
        $('.history-btn').click(add_item_cart);
    };
    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {},
        dataType: 'json',
        beforeSend: function () {
            $("#loading").show();
        },
        success: requestCallBack,
        error: function (data) {
            if (data.statusText == "FORBIDDEN") {
                window.location = "denglu2.html";
            }
        }
    });
}


function add_item_cart() {
    var item_id = $(this).attr("cid");
    var sku_id = $(this).attr("vid");
    var cart_id = $(this).attr("gid");
    var num = 1;
    var requestUrl = GLConfig.baseApiUrl + GLConfig.get_cart_url;
    var requestCallBack = function (res) {
        $("#loading").hide();
        Set_shopcarts_num();
        addShoping(cart_id);
    };

    $.ajax({
        type: 'post',
        url: requestUrl,
        data: {"num": num, "item_id": item_id, "sku_id": sku_id, "csrfmiddlewaretoken": csrftoken, "cart_id": cart_id },
        beforeSend: function () {
            $("#loading").show();
        },
        success: requestCallBack,
        error: function (data) {
            $("#loading").hide();
            if (data.status >= 300) {
                var errmsg = $.parseJSON(data.responseText).detail;
                drawToast(errmsg);
                if (errmsg == "商品库存不足") {
                    setTimeout(reload, 1000)
                }
            }
        }
    });
}

function addShoping(cart_id) {
    var $shop = $('.cart');
    var cart_image = $('#item_' + cart_id + " img");
    var x = cart_image.offset().left + 200,
        y = cart_image.offset().top,
        X = $shop.offset().left,
        Y = $shop.offset().top;

    if ($('#floatOrder').length <= 0) {
        var cart_image_url = $('#item_' + cart_id + " img").attr('src');
        $('body').append('<div id="floatOrder"><img src="' + cart_image_url + '" width="150px" /></div>');
    }
    var $obj = $('#floatOrder');

    if (!$obj.is(':animated')) {
        $obj.css({'left': x, 'top': y}).animate({'left': X + 20, 'top': Y ,'width': 10, 'height':10 }, 500, function () {
            $obj.stop(false, false).animate({'top': Y, 'opacity': 0}, 500, function () {
                $obj.fadeOut(500, function () {
                    $obj.remove();
                });
            });
        });
    }


}