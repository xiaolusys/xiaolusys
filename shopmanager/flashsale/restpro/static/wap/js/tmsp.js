/*
 *@auther:imeron
 *@date:2015-07-25
 */
//创建图片滑动插件

var settings = {
    trigger: 'click',
    title: '',
    content: '',
    width:600,
    multi: false,
    closeable: true,
    style: '',
    padding: true
};

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
    function　config_pic_url(pic_url){
		return makePicUlr(pic_url,{'size':'640' ,'format':'jpg', 'quality':'90'});
	}
    var slides = [];
    $.each(obj_list, function (index, obj) {
        slides[slides.length] = '<div class="swiper-slide"><img src="' + config_pic_url(obj) + '"></div>';
    });
    return slides;
}

function Create_product_detailsku_dom(obj) {
    //设置规格列表
    var sku_list = [];
    $.each(obj.normal_skus, function (index, sku) {
    	if (sku.is_saleout === true || !obj.is_saleopen ){
    		sku.sku_class="disable";
    	}else if(obj.normal_skus.length == 1){
    		sku.sku_class = "active";
    	}else{
    		sku.sku_class = "normal";
    	}
        sku_list[sku_list.length] = '<li class="{{sku_class}}" name="select-sku" sku_id="{{id}}" id="skusize_{{id}}" sku_price="{{agent_price}}">{{name}}<i></i></li>'.template(sku);
    });
    obj.sku_list = sku_list.join('');
    //创建商品详情及规格信息
    function Content_dom() {
        /*
         <div class="goods-info">
         <h3>{{name}}</h3>
         <div class="price">
         <span>¥ {{ product_lowest_price }}</span>
         <s>¥{{ std_sale_price }}</s>
         </div>
         <span id="product_id" style="display:none">{{id}}</span>
         </div>
         <div class="goods-size">
         <img src="http://img.xiaolumeimei.com/kexuanchima.png?imageMogr2/format/jpg/quality/100" width="100%">
         <ul id="js-goods-size">
         {{sku_list}}
         </ul>
         </div>
         */
    }

    return hereDoc(Content_dom).template(obj);
}
function add_chi_ma(obj) {
    var insertable = "";
    $.each(obj.normal_skus, function (index, sku) {
        if (sku.size_of_sku.result != "None") {
            if (index == 0) {
                insertable = "<table><tr><th>尺码</th>";
                for (var p in sku.size_of_sku.result) {
                    insertable += "<th>" + p + "</th>";
                }
                insertable += "</tr><tr><td>" + sku.name + "</td>";
                for (var p in sku.size_of_sku.result) {
                    insertable += "<td>" + sku.size_of_sku.result[p] + "</td>";
                }
                insertable += "</tr>";
            } else {
                insertable += "<tr><td>" + sku.name + "</td>";
                for (var p in sku.size_of_sku.result) {
                    insertable += "<td>" + sku.size_of_sku.result[p] + "</td>";
                }
                insertable += "</tr>";
            }
        }
    });
    if (insertable.length > 0) {
        insertable += "</table>";
        $(".chi-ma-biao").append(insertable);
    }
}
function link_sku_size(obj){
    $.each(obj.normal_skus, function (index, sku) {
        if(sku.is_saleout){
            return;
        }
        var tableContent = "";
        if (sku.size_of_sku.free_num != "NO") {
            tableContent = "<div class='remain-num' style='font-size:20px;text-align:center'><h3>仅剩下<span style='color:#f9339b'>" + sku.size_of_sku.free_num + "</span>件,不要错过哦(^_^)</h3></div>";
        }
        if (sku.size_of_sku.result != "None") {

            tableContent += "<table class='pop-class table-bordered'><tr>";
            for (var p in sku.size_of_sku.result) {
                tableContent += "<th>" + p + "</th>";
            }
            tableContent += "</tr><tr>";
            for (var p in sku.size_of_sku.result) {
                tableContent += "<td>" + sku.size_of_sku.result[p] + "</td>";
            }
            tableContent += "</tr></table>";
        }
        if (tableContent.length > 0) {
            var tableSettings = {
                content: tableContent
            };
            $('#skusize_' + sku.id).webuiPopover('destroy').webuiPopover($.extend({}, settings, tableSettings));
        }
    });
}
function Create_product_bottomslide_dom(obj_list) {
    //创建内容图Slide
    function　config_pic_url(pic_url){
		return makePicUlr(pic_url,{'size':'640' ,'format':'jpg', 'quality':'90'});
	}
    var slides = [];
    $.each(obj_list, function (index, obj) {
        slides[slides.length] = '<img src="' + config_pic_url(obj) + '">';
    });
    return slides.join('');
}

function Set_product_detail(suffix) {
    //请求URL
    var requestUrl = GLConfig.baseApiUrl + suffix;
    //请求成功回调函数
    var requestCallBack = function (data) {
    	$("#loading").hide();
        if (isNone(data.id)) {
            return;
        }
        product_model = data.product_model;
        if (isNone(product_model)) {
            product_model = data.details;
        }
        console.log('debug:',product_model);
        //设置商品题头图列表
        //弃用Create_product_topslides函数
        var pipes = [];
        if(data.watermark_op)
            pipes.push(data.watermark_op);
        pipes.push('imageMogr2/thumbnail/640/format/jpg/quality/90');
        var slide = data.pic_path + '?' + pipes.join('|');
        var slides = ['<div class="swiper-slide"><img src="' + slide + '"></div>'];
        //设置swiper滑动图片
        swiper.removeAllSlides();
        swiper.appendSlide(slides);

        //设置订单商品明细
        var detail_dom = Create_product_detailsku_dom(data);
        var params = template('params', data);
        $('.goods-content').html(detail_dom+params);

        //设置商品内容图列表
        var bottom_dom = Create_product_bottomslide_dom(product_model.content_imgs);
        $('.goods-img .list').html(bottom_dom);
        if (data.offshelf_time) {
            var shelf_time = new Date(data.offshelf_time.replace("T", " "));
            product_timer_new(shelf_time, data.is_saleopen);
        } else if (data.sale_time) {
            var shelf_time = new Date(data.sale_time);
            product_timer(shelf_time);
        }
        //设置尺码表
        add_chi_ma(data);
        if(data.is_saleopen){
            link_sku_size(data);
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


function product_timer_new(shelf_time, is_saleopen) {
    /*
     * 商品倒计时NEW
     * auther:yann
     * date:2015/28/10
     */
    var ts = (new Date(shelf_time.getFullYear(), shelf_time.getMonth(), shelf_time.getDate(), shelf_time.getHours(), shelf_time.getMinutes(), shelf_time.getSeconds())) - (new Date());//计算剩余的毫秒数

    var dd = parseInt(ts / 1000 / 60 / 60 / 24, 10);//计算剩余的天数
    var hh = parseInt(ts / 1000 / 60 / 60 % 24, 10);//计算剩余的小时数
    var mm = parseInt(ts / 1000 / 60 % 60, 10);//计算剩余的分钟数
    var ss = parseInt(ts / 1000 % 60, 10);//计算剩余的秒数
    dd = checkTime(dd);
    hh = checkTime(hh);
    mm = checkTime(mm);

    if (!is_saleopen) {
        $(".shengyu span").text("未上架");
    } else if (ts > 0) {
        $(".shengyu span").text(hh + ":" + mm + ":" + ss);
        setTimeout(function () {
                product_timer_new(shelf_time, is_saleopen);
            },
            1000);
    } else {
        $(".shengyu span").text("00:00:00");
    }
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
        $(".shengyu span").text(hh + ":" + mm + ":" + ss);
        setTimeout(function () {
                product_timer(shelf_time);
            },
            1000);
    } else {
        $(".shengyu span").text("00:00:00");
    }

}

function reload(){
    location.reload();
}
function Create_item() {
    var item_id = $("#product_id").html();
    var sku = $("#js-goods-size .active");
    var sku_id = sku.eq(0).attr("sku_id");
    var num = 1;
    var requestUrl = GLConfig.baseApiUrl + "/carts";
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
            if(data.status >= 300){
            	var errmsg = $.parseJSON(data.responseText).detail;
            	drawToast(errmsg);
                if(errmsg == "商品库存不足"){
                    setTimeout(reload, 1000);
                }
            }
        }
    });
}

function need_set_info(){
	//获取设置帐号的信息
	var requestUrl = GLConfig.baseApiUrl + "/users/need_set_info";

	var requestCallBack = function(res){
        var result = res.result;
        if(result=="yes" || result == "1"){
            $(".p-center").append('<span class="center-red-dot"></span>');
        }

	};
	// 请求推荐数据
	$.ajax({
		type:'get',
		url:requestUrl,
		data:{},
		dataType:'json',
		success:requestCallBack
	});
}
