/**
 * Created on 3/7/16.
 * 代理店铺商品展示
 */

function createProductDom(obj) {
    var product = $("#item_dom").html();
    return hereDoc(product).template(obj)
}

function createModelDom(obj) {
    var product = $("#model_dom").html();
    return hereDoc(product).template(obj)
}

function createShopHhead(obj) {
    var head = $("#shop-head").html();
    return hereDoc(head).template(obj)
}

var nextShopPage = GLConfig.baseApiUrl + GLConfig.mama_shop;
var mm_linkid_for_shop = getUrlParam('mm_linkid');

var mmshopHeadFlag = false;
var mmshopCategory = '';
var shopSaleTimeFlag = false;

$(document).ready(function () {
    console.log('link', mm_linkid_for_shop);
    if (mm_linkid_for_shop == null) {
        drawToast('店铺信息有误建议去逛逛首页吧～');
        window.location = 'http://m.xiaolumeimei.com/index.html';
        return
    }
    get_mama_shop_info();
    $(window).scroll(function () {
        loadData(get_mama_shop_info);// 更具页面下拉情况来加载数据
    });
});


function get_mama_shop_info() {
    var url = nextShopPage;
    if (url == null) {
        drawToast('逛完了,挑选几件哦~');
        return
    }

    var data = {'mm_linkid': mm_linkid_for_shop, 'category': mmshopCategory};
    var body = $(".shop-body");
    if (body.hasClass('loading')) {// 如果没有返回则　return
        return
    }
    body.addClass('loading');

    $.ajax({
        "url": url,
        "type": 'get',
        'data': data,
        "success": callback,
        "csrfmiddlewaretoken": csrftoken
    });

    function callback(res) {
        console.log('res:', res);
        body.removeClass('loading');
        // 当前时间　减去　　sale_time 转　时间格式　取最大时间　＝　剩余时间
        nextShopPage = res.next;
        if (mmshopHeadFlag == false) {
            var head = createShopHhead(res.results.shop_info);
            console.log("head:", res.results.shop_info);
            $('.action-btn').after(head);
            mmshopHeadFlag = true;
        }

        $.each(res.results.products, function (i, val) { //默认对象
            console.log("model:", val.model);
            if (val.model > 0) {
                var model_dom = createModelDom(val);
                $('.shop-body').append(model_dom);
            }
            else {
                var item_dom = createProductDom(val);
                $('.shop-body').append(item_dom);
            }


            console.log("val.offshelf_time:", val.offshelf_time);
            var offshelf_time = new Date(val.offshelf_time.replace("T", " "));
            var ts = (new Date(
                    offshelf_time.getFullYear(),
                    offshelf_time.getMonth(),
                    offshelf_time.getDate(),
                    offshelf_time.getHours(),
                    offshelf_time.getMinutes(),
                    offshelf_time.getSeconds())) - (new Date());//计算剩余的毫秒数
            if (ts > 0 && shopSaleTimeFlag == false) {
                product_timer_new(offshelf_time, true);
                shopSaleTimeFlag = true;
            }
        });
    }
}

function loadData(func) {//动态加载数据
    var totalheight = parseFloat($(window).height()) + parseFloat($(window).scrollTop()); //浏览器的高度加上滚动条的高度
    var scroll_height = $(document).height() - totalheight;
    if ($(document).height() - 600 <= totalheight && scroll_height < 600) //当文档的高度小于或者等于总的高度的时候，开始动态加载数据
    {
        func();
    }
}


function product_timer_new(shelf_time, is_saleopen) {
    var ts = (new Date(
            shelf_time.getFullYear(),
            shelf_time.getMonth(),
            shelf_time.getDate(),
            shelf_time.getHours(),
            shelf_time.getMinutes(),
            shelf_time.getSeconds())) - (new Date());//计算剩余的毫秒数
    //console.log('ts:', ts);
    var dd = parseInt(ts / 1000 / 60 / 60 / 24, 10);//计算剩余的天数
    var hh = parseInt(ts / 1000 / 60 / 60 % 24, 10);//计算剩余的小时数
    var mm = parseInt(ts / 1000 / 60 % 60, 10);//计算剩余的分钟数
    var ss = parseInt(ts / 1000 % 60, 10);//计算剩余的秒数
    dd = checkTime(dd);
    hh = checkTime(hh);
    mm = checkTime(mm);
    ss = checkTime(ss);

    if (!is_saleopen) {
        //$(".leave-time").text("");
    } else if (ts >= 86400000) {
        var html = '剩余时间<em>' + dd + '</em>天<em>' + hh + '</em>时<em>' + mm + '</em>分<em>' + ss + '</em>秒';
        $(".leave-time").empty().append(html);
        setTimeout(function () {
                product_timer_new(shelf_time, is_saleopen);
            },
            1000);
    } else if (ts < 86400000 && ts > 0) {
        var html = '剩余时间<em>' + hh + '</em>时<em>' + mm + '</em>分<em>' + ss + '</em>秒';
        $(".leave-time").empty().append(html);
        setTimeout(function () {
                product_timer_new(shelf_time, is_saleopen);
            },
            1000);
    } else if (ts < 0) {
        $(".leave-time").text("已下架");
    }

}