/**
 * Created by yann on 15-7-24.
 */

// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
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

function create_shop_carts_dom(obj) {
    function carts_dom() {
        /*
         <div class="item" id="item_{{id}}">
         <div class="gpic"><img src="{{ pic_path}}"></div>
         <div class="gname">{{ title }}</div>
         <div class="gprice">¥ <span class="item_price">{{ price}}</span></div>
         <div class="gsize">尺码：{{sku_name}}</div>
         <div class="goprice"><s>¥168</s></div>
         <div class="btn-del" id="shop_cart_{{id}}" cid="{{id}}" onclick="del_shop({{id}})"></div>
         <div class="gcount">
         <div class="btn reduce" onclick="minus_shop({{id}})"></div>
         <div class="total">
         <input type="tel" id="num_{{id}}" value="{{num}}">
         </div>
         <div class="btn plus" onclick="plus_shop({{id}})"></div>
         </div>
         </div>
         */
    };
    return hereDoc(carts_dom).template(obj)
}
//定义多行字符串函数实现
function hereDoc(f) {
    return f.toString().replace(/^[^\/]+\/\*!?\s?/, '').replace(/\*\/[^\/]+$/, '');
}

function get_shop_carts(suffix) {
    //请求URL
    var requestUrl = GLConfig.baseApiUrl + suffix;

    //请求成功回调函数
    var requestCallBack = function (data) {
        var total_price = 0;
        if (data.count != 'undefined' && data.count != null) {
            $.each(data.results,
                function (index, product) {
                    total_price += product.total_fee;
                    var cart_dom = create_shop_carts_dom(product);
                    $('.cart-list').append(cart_dom);
                }
            );
        }
        $("#total_price").html(total_price);
    };
    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {},
        dataType: 'json',
        success: requestCallBack
    });
}

function del_shop(id) {
    var suffix = "/carts/" + id + "/delete_carts";
    var requestUrl = GLConfig.baseApiUrl + suffix;
    console.log(csrftoken);
    var item_id = $("#item_" + id);
    var requestCallBack = function (data) {
        item_id.remove();
        var prices = $(".item_price");
        //重新计算总价格
        var total_price = 0;
        $.each(prices, function (index, product) {
                total_price += parseFloat(prices.eq(index).html());
            }
        );
        $("#total_price").html(total_price);
    };
    // 发送请求
    $.ajax({
        type: 'post',
        url: requestUrl,
        data: {"csrfmiddlewaretoken": csrftoken},
        success: requestCallBack
    });
}

function plus_shop(id) {
    var suffix = "/carts/" + id + "/plus_product_carts";
    var requestUrl = GLConfig.baseApiUrl + suffix;
    var num_id = $("#num_" + id);
    var requestCallBack = function (res) {
        console.log(res);
        if (res == "1") {
            num_id.val(parseInt(num_id.val()) + parseInt(res));
        }

    };
    // 发送请求
    $.ajax({
        type: 'post',
        url: requestUrl,
        data: {"csrfmiddlewaretoken": csrftoken},
        success: requestCallBack
    });
}
function minus_shop(id) {
    var suffix = "/carts/" + id + "/minus_product_carts";
    var requestUrl = GLConfig.baseApiUrl + suffix;
    var num_id = $("#num_" + id);
    var requestCallBack = function (res) {
        console.log(res);
        if (res == "1") {
            num_id.val(parseInt(num_id.val()) - parseInt(res));
        }

    };
    // 发送请求
    if (num_id.val() != "1") {
        $.ajax({
            type: 'post',
            url: requestUrl,
            data: {"csrfmiddlewaretoken": csrftoken},
            success: requestCallBack
        });
    }
}
$(function () {
    $(".btn-del").click(function () {
        alert("Hello World  click");
    });
});

