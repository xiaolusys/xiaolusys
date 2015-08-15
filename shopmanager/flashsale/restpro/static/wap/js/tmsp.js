/*
 *@auther:imeron
 *@date:2015-07-25
 */
//创建图片滑动插件
var swiper = new Swiper('.swiper-container', {
    pagination: '.swiper-pagination',
    paginationClickable: true,
    speed: 500, //设置动画持续时间500ms
    freeMode: true, //开启自由模式
    freeModeFluid: true, //开启'fluid'自由模式
    centeredSlides: true,
    autoplay: 2500,
    autoplayDisableOnInteraction: false
});

function Create_product_topslides(obj_list) {
    //创建商品题头图Slide
    var slides = [];
    $.each(obj_list, function (index, obj) {
        slides[slides.length] = '<div class="swiper-slide"><img src="' + obj + '"></div>';
    });
    return slides;
}

function Create_product_detailsku_dom(obj) {
    //设置规格列表
    var sku_list = [];
    $.each(obj.normal_skus, function (index, sku) {
    	sku.sku_class = "normal";
    	if (sku.is_saleout === true || !obj.is_saleopen ){
    		sku.sku_class="disable";
    	}
        sku_list[sku_list.length] = '<li class="{{sku_class}}" name="select-sku" sku_id="{{id}}" sku_price="{{agent_price}}">{{name}}<i></i></li>'.template(sku);
    });

    obj.sku_list = sku_list.join('');
    //创建商品详情及规格信息
    function Content_dom() {
        /*
         <div class="goods-info">
         <h3>{{name}}</h3>
         <div class="price">
         <span>¥ {{ agent_price }}</span>
         <s>¥{{ std_sale_price }}</s>
         </div>
         <span id="product_id" style="display:none">{{id}}</span>
         </div>
         <div class="goods-size">
         <h3>尺寸</h3>
         <ul id="js-goods-size">
         {{sku_list}}
         </ul>
         </div>
         <div class="goods-param">
         <h3>商品参数</h3>
         <table cellpadding="0" cellspacing="0">
         <tr>
         <td>商品名称</td>
         <td>{{name}}</td>
         </tr>
         <tr>
         <td>洗涤说明</td>
         <td>30℃以下手洗；阴凉处悬挂晾干</td>
         </tr>
         <tr>
         <td>备<span class="space"></span>注</td>
         <td>{{memo}}</td>
         </tr> 
         <tr>
         <td>货品编号</td>
         <td>{{outer_id}}</td>
         </tr>
         </table>
         </div>
         */
    }

    return hereDoc(Content_dom).template(obj);
}

function Create_product_bottomslide_dom(obj_list) {
    //创建内容图Slide
    var slides = [];
    $.each(obj_list, function (index, obj) {
        slides[slides.length] = '<img src="' + obj + '">';
    });
    return slides.join('');
}

function Set_product_detail(suffix) {
    //请求URL
    var requestUrl = GLConfig.baseApiUrl + suffix;
    //请求成功回调函数
    var requestCallBack = function (data) {
    	$("#loading").hide();
        if (data.id == 'undifine' && data.id == null) {
            return
        }
        product_model = data.product_model;
        if (isNone(product_model)) {
            product_model = data.details;
        }
        console.log('debug:',product_model);
        //设置商品题头图列表
        var slides = Create_product_topslides(product_model.head_imgs);
        //设置swiper滑动图片
        swiper.removeAllSlides();
        swiper.appendSlide(slides);

        //设置订单商品明细
        var detail_dom = Create_product_detailsku_dom(data);
        $('.goods-content').html(detail_dom);
        //设置商品内容图列表
        var bottom_dom = Create_product_bottomslide_dom(product_model.content_imgs);
        $('.goods-img .list').html(bottom_dom);
        if(data.sale_time){
            var shelf_time = new Date(data.sale_time);
            product_timer(shelf_time);
        }
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
        success: requestCallBack
    });
}

function product_timer(shelf_time) {
    /*
     * 商品倒计时
     * auther:yann
     * date:2015/15/8
     */
    var ts = (new Date(shelf_time.getFullYear(), shelf_time.getMonth(), shelf_time.getDate() + 1, 14, 0, 0)) - (new Date());//计算剩余的毫秒数

    var hh = parseInt(ts / 1000 / 60 / 60 , 10);//计算剩余的小时数
    var mm = parseInt(ts / 1000 / 60 % 60, 10);//计算剩余的分钟数
    var ss = parseInt(ts / 1000 % 60, 10);//计算剩余的秒数

    hh = checkTime(hh);
    mm = checkTime(mm);
    ss = checkTime(ss);

    if (ts > 0) {
        $(".shengyu span").text(hh + "时" + mm + "分" + ss + "秒");
        setTimeout(function () {
                product_timer(shelf_time);
            },
            1000);
    } else {
        $(".shengyu span").text("00:00");
    }

}

function reload(){
    location.reload();
}
function Create_item() {
    var item_id = $("#product_id").html();
    var sku = $("#js-goods-size .active");
    if (sku.length > 0) {
        var sku_id = sku.eq(0).attr("sku_id");
        var num = 1;
        var requestUrl = GLConfig.baseApiUrl + "/carts"
        var requestCallBack = function (res) {
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
                if(data.status==500){
                    if($.parseJSON(data.responseText).detail=="商品库存不足"){
                        drawToast("商品库存不足");
                        setTimeout(reload,1000)
                    }
                }
                if (data.statusText == "FORBIDDEN") {
                    window.location = "denglu.html";
                }
            }
        });
    }
}

