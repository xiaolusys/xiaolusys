/**
 * Created by yann on 15-7-24.
 */

function update_total_price() {
    var prices = $(".item_price");
    var total_price = 0;
    $.each(prices, function (index, price) {
            price_id = prices.eq(index).attr("id");
            item_id = price_id.split("_")[1];
            total_price += parseFloat(prices.eq(index).html()) * parseInt($("#num_" + item_id).val());
        }
    );
    $("#total_price").html(total_price.toFixed(2));
}
function get_shop_carts(suffix) {
    /*
     * 获取购物车内容
     * auther:yann
     * date:2015/1/8
     */
    //请求URL
    var requestUrl = GLConfig.baseApiUrl + suffix;

    //请求成功回调函数
    var requestCallBack = function (data) {
        var total_price = 0;
        $("#loading").hide();
        $(".buy").show();
        $('.cart-list').empty();
        if (data && data.length > 0) {
            $.each(data,
                function (index, product) {
                    total_price += product.price * product.num;
                    var html = template('item_template', product);
                    $('.cart-list').append(html);
                }
            );
        } else {
            window.location = "gouwuche-kong.html";
        }
        $("#total_price").html(total_price.toFixed(2));
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
            console.info("error: " + data.statusText);
        }
    });
}

function del_shop(id) {
    var suffix = "/carts/" + id + "/delete_carts";
    var requestUrl = GLConfig.baseApiUrl + suffix;
    var item_id = $("#item_" + id);
    var requestCallBack = function (res) {
        get_shop_carts(GLConfig.get_cart_url);
    };

    swal({
            title: "",
            text: "删掉的商品可能被别人抢走哦～\n要删除吗？",
            type: "",
            showCancelButton: true,
            imageUrl: "http://img.xiaolumeimei.com/logo.png",
            confirmButtonColor: '#DD6B55',
            confirmButtonText: '删除',
            cancelButtonText: '先留着'
        },
        function () {
            //发送请求
            $.ajax({
                type: 'post',
                url: requestUrl,
                data: {"csrfmiddlewaretoken": csrftoken},
                success: requestCallBack,
                error: function (res) {
                    get_shop_carts(GLConfig.get_cart_url);
                }
            });
        });


}

function plus_shop(id) {
    var suffix = "/carts/" + id + "/plus_product_carts";
    var requestUrl = GLConfig.baseApiUrl + suffix;
    var num_id = $("#num_" + id);
    var requestCallBack = function (res) {
        $("#loading").hide();
        if (res.status == "1") {
            num_id.val(parseInt(num_id.val()) + parseInt(res.status));
            update_total_price();
        }
    };
    // 发送请求
    $.ajax({
        type: 'post',
        url: requestUrl,
        data: {"csrfmiddlewaretoken": csrftoken},
        beforeSend: function () {
            $("#loading").show();
        },
        success: requestCallBack,
        error: function (err) {
            $("#loading").hide();
            var resp = JSON.parse(err.responseText);
            if (!isNone(resp.detail)) {
                drawToast(resp.detail);
            }
        }
    });
}
function minus_shop(id) {
    var suffix = "/carts/" + id + "/minus_product_carts";
    var requestUrl = GLConfig.baseApiUrl + suffix;
    var num_id = $("#num_" + id);
    var requestCallBack = function (res) {
        $("#loading").hide();
        if (res.status == "1") {
            num_id.val(parseInt(num_id.val()) - parseInt(res.status));
            update_total_price();
        }

    };
    // 发送请求
    if (num_id.val() != "1") {
        $.ajax({
            type: 'post',
            url: requestUrl,
            data: {"csrfmiddlewaretoken": csrftoken},
            beforeSend: function () {
                // 禁用按钮防止重复提交,加载页面
                $("#loading").show();
            },
            success: requestCallBack,
            error: function (err) {
                var resp = JSON.parse(err.responseText);
                if (!isNone(resp.detail)) {
                    drawToast(resp.detail);
                }
            }
        });
    } else {
        drawToast("客官至少买一件嘛");
    }
}

get_remain_time();
function get_remain_time() {
    /*
     * 得到购物车数量
     * auther:yann
     * date:2015/13/8
     */
    var requestUrl = GLConfig.baseApiUrl + GLConfig.get_num_cart;
    var requestCallBack = function (res) {
        var newDate = new Date();
        if (res.last_created > 0) {
            newDate.setTime(res.last_created * 1000);
            cart_timer(newDate)
        }
    };
    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: "",
        beforeSend: function () {
            
        },
        success: requestCallBack,
        error: function (data) {
            console.log('debug cartnum:', data);
            if (data.status == 403) {
                $(".total").html("0");
            }
        }
    });
}

function cart_timer(remain_date) {
    /*
     * 购物车倒计时
     * auther:yann
     * date:2015/13/8
     */
    var ts =  remain_date - (new Date());//计算剩余的毫秒数
    var mm = parseInt(ts / 1000 / 60 % 60, 10);//计算剩余的分钟数
    var ss = parseInt(ts / 1000 % 60, 10);//计算剩余的秒数
    mm = checkTime(mm);
    ss = checkTime(ss);
    console.log("sss",ts);
    if (ts > 0) {
        $("#remain_time").text( mm + ":" + ss);
        setTimeout(function () {
                cart_timer(remain_date);
            },
            1000);
    } else {
        $("#remain_time").text("");
    }

}
function checkTime(i) {
    if (i < 10) {
        i = "0" + i;
    }
    return i;
}