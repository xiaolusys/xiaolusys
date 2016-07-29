/**
 * Created by jishu_linjie on 9/7/15.
 */
/**
 *@author: imeron
 *@date: 2015-07-22
 */
var timestamp = Date.parse(new Date());
var wait = 60;
function time(btn) {
    if (wait == 0) {
        btn.click(get_code);
        btn.text("获取验证码");
        wait = 60;
    } else {
        btn.unbind("click");
        btn.text(wait + "秒后重新获取");
        wait--;
        setTimeout(function () {
                time(btn);
            },
            1000);
    }
}

var today = new Date();
function today_timer() {
    /*
     * 首页(今日)倒计时
     * auther:yann
     * date:2015/6/8
     */
    var ts = (new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1, 14, 0, 0)) - (new Date());//计算剩余的毫秒数
    var dd = parseInt(ts / 1000 / 60 / 60 / 24, 10);//计算剩余的天数
    var hh = parseInt(ts / 1000 / 60 / 60 % 24, 10);//计算剩余的小时数
    var mm = parseInt(ts / 1000 / 60 % 60, 10);//计算剩余的分钟数
    var ss = parseInt(ts / 1000 % 60, 10);//计算剩余的秒数
    dd = checkTime(dd);
    hh = checkTime(hh);
    mm = checkTime(mm);
    ss = checkTime(ss);

    if (ts > 100800000 && ts < 136800000) {
        $(".poster_timer.tm2").text("敬请期待");
    } else if (ts < 100800000 && ts >= 86400000) {
        $(".poster_timer.tm2").text("剩余" + dd + "天" + hh + "时" + mm + "分" + ss + "秒");
        setTimeout(function () {
                today_timer();
            },
            1000);
    } else if (ts < 86400000) {
        $(".poster_timer.tm2").text("剩余" + hh + "时" + mm + "分" + ss + "秒");
        setTimeout(function () {
                today_timer();
            },
            1000);
    }

}

function yesterday_timer() {
    /*
     * 昨日特卖倒计时
     * auther:yann
     * date:2015/6/8
     */
    var ts = (new Date(today.getFullYear(), today.getMonth(), today.getDate(), 14, 0, 0)) - (new Date());//计算剩余的毫秒数
    var dd = parseInt(ts / 1000 / 60 / 60 / 24, 10);//计算剩余的天数
    var hh = parseInt(ts / 1000 / 60 / 60 % 24, 10);//计算剩余的小时数
    var mm = parseInt(ts / 1000 / 60 % 60, 10);//计算剩余的分钟数
    var ss = parseInt(ts / 1000 % 60, 10);//计算剩余的秒数
    dd = checkTime(dd);
    hh = checkTime(hh);
    mm = checkTime(mm);
    ss = checkTime(ss);
    console.log(dd, hh, mm, ss);
    if (ts > 0) {
        $(".poster_timer.tm2").text(hh + "时" + mm + "分" + ss + "秒");
        setTimeout(function () {
                yesterday_timer();
            },
            1000);
    } else {
        $(".poster_timer.tm2").text("敬请期待明日上新");
    }
}
function tm_timer_today() {
    /*
     * 今天海报特卖倒计时
     * auther:yann
     * date:2015/20/8
     */
    var ts = (new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1, 14, 0, 0)) - (new Date());//计算剩余的毫秒数
    var dd = parseInt(ts / 1000 / 60 / 60 / 24, 10);//计算剩余的天数
    var hh = parseInt(ts / 1000 / 60 / 60 % 24, 10);//计算剩余的小时数
    var mm = parseInt(ts / 1000 / 60 % 60, 10);//计算剩余的分钟数
    var ss = parseInt(ts / 1000 % 60, 10);//计算剩余的秒数
    dd = checkTime(dd);
    hh = checkTime(hh);
    mm = checkTime(mm);
    ss = checkTime(ss);
    if (ts > 100800000 && ts < 136800000) {
        $(".poster_timer.tm1").text("敬请期待");
    } else if (ts < 100800000 && ts >= 86400000) {
        $(".poster_timer.tm1").text("剩余" + dd + "天" + hh + "时" + mm + "分" + ss + "秒");
        setTimeout(function () {
                tm_timer_today();
            },
            1000);
    } else if (ts < 86400000) {
        $(".poster_timer.tm1").text("剩余" + hh + "时" + mm + "分" + ss + "秒");
        setTimeout(function () {
                tm_timer_today();
            },
            1000);
    }
}
function tm_timer() {
    /*
     * 昨日海报特卖倒计时
     * auther:yann
     * date:2015/20/8
     */
    var ts = (new Date(today.getFullYear(), today.getMonth(), today.getDate(), 14, 0, 0)) - (new Date());//计算剩余的毫秒数
    var dd = parseInt(ts / 1000 / 60 / 60 / 24, 10);//计算剩余的天数
    var hh = parseInt(ts / 1000 / 60 / 60 % 24, 10);//计算剩余的小时数
    var mm = parseInt(ts / 1000 / 60 % 60, 10);//计算剩余的分钟数
    var ss = parseInt(ts / 1000 % 60, 10);//计算剩余的秒数
    dd = checkTime(dd);
    hh = checkTime(hh);
    mm = checkTime(mm);
    ss = checkTime(ss);
    console.log(dd, hh, mm, ss);
    if (ts >= 86400000) {
        $(".poster_timer.tm1").text("剩余" + dd + "天" + hh + "时" + mm + "分" + ss + "秒");
        setTimeout(function () {
                tm_timer();
            },
            1000);
    } else if (ts < 86400000 && ts > 0) {
        $(".poster_timer.tm1").text("剩余" + hh + "时" + mm + "分" + ss + "秒");
        setTimeout(function () {
                tm_timer();
            },
            1000);
    } else {
        $(".poster_timer.tm1").text("敬请期待");
    }
}
function checkTime(i) {
    if (i < 10) {
        i = "0" + i;
    }
    return i;
}

function Set_posters(suffix) {
    //获取海报
    var posterUrl = GLConfig.baseApiUrl + suffix;
    var posterCallBack = function (data) {
        if (!isNone(data.wem_posters)) {
            //设置女装海报链接及图片
            $.each(data.wem_posters,
                function (index, poster) {
                    $('.poster .nvzhuang').attr('href', poster.item_link);
                    $('.poster .nvzhuang img').attr('src', poster.pic_link + "?imageMogr2/thumbnail/289/format/jpg/quality/90");
                    if (poster.subject === 'undifine' || poster.subject === null) {
                        return;
                    }
                    //$('.poster .nvzhuang .subject').html('<span class="tips">'+poster.subject[0]+'</span>'+poster.subject[1]);
                }
            );
        }

        if (!isNone(data.chd_posters)) {
            //设置童装海报链接及图片
            $.each(data.chd_posters,
                function (index, poster) {
                    $('.poster .chaotong').attr('href', poster.item_link);
                    $('.poster .chaotong img').attr('src', poster.pic_link + "?imageMogr2thumbnail/618/format/jpg/quality/95");
                    if (poster.subject === 'undifine' || poster.subject === null) {
                        return;
                    }
                    //$('.poster .chaotong .subject').html('<span class="tips">'+poster.subject[0]+'</span>'+poster.subject[1]);
                }
            );
        }
    };
    // 请求海报数据
    $.ajax({
        type: 'get',
        url: posterUrl,
        data: {},
        dataType: 'json',
        success: posterCallBack
    });
}

function Create_verify_icon(obj){
    var html = $("#verify_icon").html();
    return hereDoc(html).template(obj);
}

function preview_verify(verify, id, dom, model_id, sale_charger) {
    var not_verify_icon = "images/tuihuo-jujue.png";//没有审核图标
    var already_verify_icon = "images/icon-ok.png";//已经审核图标
    var multi_icon = "images/preview-duokuan.png";//多款图标
    //如果是同款页面则不显示多款的icon // sale_charger  归属采购员
    var current_url = window.location.href.split('?')[0].split("/");
    var redom = "";
    var icon = "";
    var obj = {"id":id,"model_id":model_id,"sale_charger":sale_charger};
    if (current_url[current_url.length - 1] == "tongkuan-preview.html") {
        if (verify == false)//如果审核状态不是true,即没有审核，或者被修改状态
        {   obj.icon = not_verify_icon;
            icon = Create_verify_icon(obj);
            redom = $(dom).append(icon);
        }
        else if(verify == true){
            obj.icon = already_verify_icon;
            icon = Create_verify_icon(obj);
            redom = $(dom).append(icon);
        }
    }
    else {//不是同款页面
        if (verify == false && model_id == null)//如果审核状态不是true,即没有审核，或者被修改状态
        {
            obj.model_id = 0;
            obj.icon = not_verify_icon;
            icon = Create_verify_icon(obj);
            redom = $(dom).append(icon);
        }
        else if (verify == true && model_id == null) {
            obj.model_id = 0;
            obj.icon = already_verify_icon;
            icon = Create_verify_icon(obj);
            redom = $(dom).append(icon);
        }
        else {
            obj.icon = multi_icon;
            icon = Create_verify_icon(obj);
            redom = $(dom).append(icon);
        }
        //如果同款多个产品的话查看是否所有产品都审核通过　如果所有的都通过了审核则显示对应图片
        if (model_id != null) {
            var modelUrl = GLConfig.baseApiUrl + GLConfig.get_modellist_url.template({'model_id': model_id});
            $.ajax({
                type: 'get',
                url: modelUrl,
                data: {},
                dataType: 'json',
                success: modelCallBack
            });
            var flag = 1;
            function modelCallBack(res) {
                $.each(res, function (index, obj) {
                    if (obj.is_verify == false) {
                        flag = 0;
                    }
                });
                if (flag) {
                    $("#previev_vierify_" + id).attr("src", "images/icon-ok.png");
                }
            }
        }
    }
    return redom;
}

function verify_categray(id, model_id) {
    //判断是否存在多款，model_id
    // 如果在同款页面则不去判断是否跳转
    console.log("商品id:",id,"款式id:",model_id);
    var current_url = window.location.href.split('?')[0].split("/");
    if (current_url[current_url.length - 1] == "tongkuan-preview.html") {
        verify_action(id); //直接审核
    }
    else if (model_id != 0) {//如果不是单款
        //跳转到同款页面
        window.location = "/static/wap/tongkuan-preview.html?id=" + model_id;
    }
    else {//是单款情况下则在当前页面去修改is_verify状态
        verify_action(id);
    }
}
function verify_action(id) {
    var data = {'csrfmiddlewaretoken': getCSRF()};
    var verifyurl = GLConfig.baseApiUrl + GLConfig.verify_product.template({"id": id});
    swal({
            title: "",
            text: '你确定修改该预览审核状态吗？',
            type: "",
            showCancelButton: true,
            imageUrl: "http://img.xiaolumeimei.com/logo.png",
            confirmButtonColor: '#DD6B55',
            confirmButtonText: "确定",
            cancelButtonText: "取消"
        },
        function modify_is_verify() {//确定　则跳转
            $.ajax({
                "url": verifyurl,
                "data": data,
                "type": "post",
                dataType: 'json',
                success: requetCall,
                error: function (resp) {
                    if (resp.status == 403) {
                        // 跳转到登陆
                        var redirectUrl = window.location.href;
                        window.location = GLConfig.login_url + '?next=' + encodeURIComponent(redirectUrl);
                    }
                }
            });
        }
    );

    function requetCall(res) {
        console.log("debug verify res:", res);
        if (res.is_verify == true) {//切换图标
            $("#previev_vierify_" + id).attr("src", "images/icon-ok.png");
        }
        else if (res.is_verify == false) {
            $("#previev_vierify_" + id).attr("src", "images/tuihuo-jujue.png");
        }
    }
}

function Create_item_dom(p_obj, close_model) {

    //创建商品DOM
    function Item_dom() {
        /*
         <li>
         <a href="pages/shangpinxq.html?id={{ id }}">
         <img src="{{ head_img }}">
         <p class="gname">{{ name }}</p>
         <p class="gprice">
         <span class="nprice"><em>¥</em> {{ product_lowest_price }} </span>
         <s class="oprice"><em>¥</em> {{ std_sale_price }}</s>
         </p>{{ saleout_dom }}
         </a>
         </li>
         */
    };

    //创建商品款式DOM
    function Model_dom() {
        /*
         <li>
         <a href="tongkuan.html?id={{ product_model.id }}">
         <img src="{{ product_model.head_img }}">
         <p class="gname">{{ product_model.name }}</p>
         <p class="gprice">
         <span class="nprice"><em>¥</em> {{ lowest_price }} </span>
         <s class="oprice"><em>¥</em> {{ std_sale_price }}</s>
         </p>{{ saleout_dom }}
         </a>
         </li>
         */
    };

    p_obj.saleout_dom = '';
    var pipes = [];
    var today = new Date().Format("yyyy-MM-dd");

    //如果没有close model,并且model_product存在
    if (!close_model && !isNone(p_obj.product_model)) {
        if (!p_obj.is_saleopen) {
            if (p_obj.sale_time >= today) {
                p_obj.saleout_dom = '<div class="mask"></div><div class="text">即将开售</div>';
            } else {
                p_obj.saleout_dom = '<div class="mask"></div><div class="text">已抢光</div>';
            }
        }

        if(p_obj.watermark_op)
            pipes.push(p_obj.watermark_op);
        pipes.push('imageMogr2/thumbnail/289x289/format/jpg/quality/85');
        p_obj.product_model.head_img = p_obj.product_model.head_imgs[0] + '?' + pipes.join('|');
        return hereDoc(Model_dom).template(p_obj);
    }

    //上架判断
    if (!p_obj.is_saleopen) {
        if (p_obj.sale_time >= today) {
            p_obj.saleout_dom = '<div class="mask"></div><div class="text">即将开售</div>';
        } else {
            p_obj.saleout_dom = '<div class="mask"></div><div class="text">已抢光</div>';
        }
    } else if (p_obj.is_saleout) {
        p_obj.saleout_dom = '<div class="mask"></div><div class="text">已抢光</div>';
    }
    if (close_model && true) {
        p_obj.head_img = p_obj.pic_path;
    }

    if(p_obj.watermark_op)
        pipes.push(p_obj.watermark_op);
    pipes.push('imageMogr2/thumbnail/289x289/format/jpg/quality/85');
    p_obj.head_img += '?' + pipes.join('|');
    return hereDoc(Item_dom).template(p_obj);
}

function Set_promotes_product() {
    //预览商品列表
    var pageNum  = 1;
    var nextPage = true;
    var loading  = false;
    function get_products(suffix){
        if (nextPage == null){
           drawToast("没有更多商品了");
           return;
        };
        if (loading == true){
            return;
        }
        loading = true;
        var promoteUrl = GLConfig.baseApiUrl + suffix + '&page='+pageNum+'&page_size=10';
        var promoteCallBack = function (data) {
            $("#loading").hide();
            loading = false;
            // 这里判断　next　的页数　如果大于　pageNum　一样才去加载
            if (isNone(data.results)) {
                nextPage = null;
                return;
            }
            pageNum += 1;
            nextPage = data.next;
            $('.child_zone').hide();
            $.each(data.results,
                function (index, p_obj) {
                    if (p_obj.category.parent_cid == 8 || p_obj.category.cid == 8) {
                        var item_dom = Create_item_dom(p_obj);
                        item_dom = preview_verify(p_obj.is_verify, p_obj.id, item_dom, p_obj.model_id,p_obj.sale_charger);
                        $('.glist .nvzhuang').append(item_dom);
                    }
                    else {
                        // 童装dom　show
                        $('.child_zone').show();
                        var child_item_dom = Create_item_dom(p_obj);
                        child_item_dom = preview_verify(p_obj.is_verify, p_obj.id, child_item_dom, p_obj.model_id,p_obj.sale_charger);
                        $('.glist .chaotong').append(child_item_dom);
                    }
                }
            );
        };
        // 请求推荐数据
        $.ajax({
            type:'get',
            url:promoteUrl,
            data:{},
            dataType:'json',
            beforeSend: function () {
                $("#loading").show();
            },
            success:promoteCallBack,
            error: function (data) {
                drawToast("数据没有加载成功！");
                $("#loading").hide();
                loading = false;
            }
        });
    }
    return get_products;
}

function Set_category_product(suffix) {
    //获取潮流童装商品
    var promoteUrl = GLConfig.baseApiUrl + suffix;

    var promoteCallBack = function (data) {
        if (!isNone(data.results)) {
            $("#loading").hide();
            //设置女装推荐链接及图片
            $.each(data.results,
                function (index, p_obj) {
                    var item_dom = Create_item_dom(p_obj, false);
                    $('.glist').append(item_dom);
                }
            );
        }
    };
    // 请求推荐数据
    $.ajax({
        type: 'get',
        url: promoteUrl,
        data: {},
        dataType: 'json',
        beforeSend: function () {
            $("#loading").show();
        },
        success: promoteCallBack
    });

}

function Set_model_product(suffix) {
    //获取同款式商品列表
    var promoteUrl = GLConfig.baseApiUrl + suffix;

    var promoteCallBack = function (data) {
        $("#loading").hide();
        //设置女装推荐链接及图片

        $.each(data,
            function (index, p_obj) {
                var item_dom = Create_item_dom(p_obj, true);
                item_dom = preview_verify(p_obj.is_verify, p_obj.id, item_dom, p_obj.model_id,p_obj.sale_charger);
                $('.glist').append(item_dom);
            }
        );
        if (data && data.length > 0 && data[0].sale_time) {
            var shelf_time = new Date(data[0].sale_time);
            product_timer(shelf_time);
        }
    };
    // 请求推荐数据
    $.ajax({
        type: 'get',
        url: promoteUrl,
        data: {},
        dataType: 'json',
        beforeSend: function () {
            $("#loading").show();
        },
        success: promoteCallBack
    });

}

function product_timer(shelf_time) {
    /*
     * 商品倒计时
     * auther:yann
     * date:2015/15/8
     */
    var ts = (new Date(shelf_time.getFullYear(), shelf_time.getMonth(), shelf_time.getDate() + 1, 14, 0, 0)) - (new Date());//计算剩余的毫秒数

    var dd = parseInt(ts / 1000 / 60 / 60 / 24, 10);//计算剩余的天数
    var hh = parseInt(ts / 1000 / 60 / 60 % 24, 10);//计算剩余的小时数
    var mm = parseInt(ts / 1000 / 60 % 60, 10);//计算剩余的分钟数
    var ss = parseInt(ts / 1000 % 60, 10);//计算剩余的秒数
    dd = checkTime(dd);
    hh = checkTime(hh);
    mm = checkTime(mm);
    ss = checkTime(ss);

    if (ts > 100800000 && ts < 136800000) {
        $(".top p").text("敬请期待");
    } else if (ts < 100800000 && ts >= 86400000) {
        $(".top p").text("剩余" + dd + "天" + hh + "时" + mm + "分");
        setTimeout(function () {
                product_timer(shelf_time);
            },
            2000);
    } else if (ts < 86400000 && ts > 0) {
        $(".top p").text("剩余" + hh + "时" + mm + "分");
        setTimeout(function () {
                product_timer(shelf_time);
            },
            2000);
    } else if (ts < 0) {
        $(".top p").text("已下架");
    }

}

/*
 * 时间格式化
 * auther:yann
 * date:2015/22/8
 */
Date.prototype.Format = function (fmt) {
    var o = {
        "M+": this.getMonth() + 1, //月份
        "d+": this.getDate(), //日
        "h+": this.getHours(), //小时
        "m+": this.getMinutes(), //分
        "s+": this.getSeconds(), //秒
        "q+": Math.floor((this.getMonth() + 3) / 3), //季度
        "S": this.getMilliseconds() //毫秒
    };
    if (/(y+)/.test(fmt)) fmt = fmt.replace(RegExp.$1, (this.getFullYear() + "").substr(4 - RegExp.$1.length));
    for (var k in o)
        if (new RegExp("(" + k + ")").test(fmt)) fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]) : (("00" + o[k]).substr(("" + o[k]).length)));
    return fmt;
}


function need_set_info() {
    //获取设置帐号的信息
    var requestUrl = GLConfig.baseApiUrl + "/users/need_set_info";

    var requestCallBack = function (res) {
        var result = res.result;
        if (result == "yes") {
            $(".p-center").append('<span class="center-red-dot"></span>');
        }
    };
    // 请求推荐数据
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {},
        dataType: 'json',
        success: requestCallBack
    });
}
