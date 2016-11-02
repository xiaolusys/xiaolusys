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

function Set_posters(suffix){
    //获取海报
    var posterUrl = GLConfig.baseApiUrl + suffix;
    function config_pic_url(pic_url){
        return makePicUlr(pic_url,{'size':'618x253','format':'jpg', 'quality':'90'});
    }
    var posterCallBack = function(data){
        if (!isNone(data.wem_posters)){
            //设置女装海报链接及图片
            $.each(data.wem_posters,
                function(index,poster){
                    $('.poster .nvzhuang').attr('href',poster.item_link);
                    $('.poster .nvzhuang img').attr('src',config_pic_url(poster.pic_link));
                    if (isNone(poster.subject))return;
                    $('.poster .nvzhuang .subject').html('<span class="tips">'+poster.subject[0]+'</span>'+poster.subject[1]);
                }
            );
        }
        if (!isNone(data.chd_posters)){
            //设置童装海报链接及图片
            $.each(data.chd_posters,
                function(index,poster){
                    $('.poster .chaotong').attr('href',poster.item_link);
                    $('.poster .chaotong img').attr('src',config_pic_url(poster.pic_link));
                    if (isNone(poster.subject))return;
                    $('.poster .chaotong .subject').html('<span class="tips">'+poster.subject[0]+'</span>'+poster.subject[1]);
                }
            );
        }
    };
    // 请求海报数据
    $.ajax({
        type:'get',
        url:posterUrl,
        data:{},
        dataType:'json',
        success:posterCallBack
    });
}

function Create_item_dom(p_obj,close_model){
    /*
     * close_model:取消款式首图展示.
     */
    //创建商品DOM
    function Item_dom(){
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
    function Model_dom(){
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
    // 图片处理管道
    var pipes = [];
    var today = new Date().Format("yyyy-MM-dd");
    var is_single_spec = isNone(p_obj.product_model) || p_obj.product_model.is_single_spec == true;
    //如果没有close model,并且model_product存在并且是多规格
    if (!close_model && is_single_spec == false) {
        if (!p_obj.is_saleopen) {
            if (p_obj.sale_time >= today) {
                p_obj.saleout_dom = '<div class="mask"></div><div class="text">即将开售</div>';
            } else {
                p_obj.saleout_dom = '<div class="mask"></div><div class="text">已抢光</div>';
            }
        }else if(p_obj.product_model.is_sale_out && true){
            p_obj.saleout_dom = '<div class="mask"></div><div class="text">已抢光</div>';
        }

        if(p_obj.watermark_op)
            pipes.push(p_obj.watermark_op);
        pipes.push('imageMogr2/thumbnail/289/format/jpg/quality/90');
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
    // 商品售光，并且单款或者同款页展示为true
    } else if (p_obj.is_saleout && (is_single_spec == true || close_model)) {
        p_obj.saleout_dom = '<div class="mask"></div><div class="text">已抢光</div>';
    }
    if (close_model && true){
        p_obj.head_img = p_obj.pic_path;
    }

    if(p_obj.watermark_op)
        pipes.push(p_obj.watermark_op);
    pipes.push('imageMogr2/thumbnail/289/format/jpg/quality/90');
    p_obj.head_img += '?' + pipes.join('|');
    return hereDoc(Item_dom).template(p_obj);
}

function Set_promotes_product(suffix){
    //获取今日推荐商品
    var promoteUrl = GLConfig.baseApiUrl + suffix;
    var promoteCallBack = function(data){
        $("#loading").hide();
        if (!isNone(data.female_list)){
            $('.glist .nvzhuang').empty();
            //设置女装推荐链接及图片
            $.each(data.female_list,
                function(index,p_obj){
                    var item_dom = Create_item_dom(p_obj);
                    $('.glist .nvzhuang').append(item_dom);
                }
            );
        }
        if (!isNone(data.child_list)){
            $('.glist .chaotong').empty();
            //设置童装推荐链接及图片
            $.each(data.child_list,
                function(index,p_obj){
                    var item_dom = Create_item_dom(p_obj);
                    $('.glist .chaotong').append(item_dom);
                }
            );
        }
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
        success:promoteCallBack
    });
}

function Set_promotes_product_by_paging(suffix){
    //通过分页获取商品数据，闭包实现
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
        var promoteUrl = GLConfig.baseApiUrl + suffix + '?page='+pageNum+'&page_size=10';
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
                        $('.glist .nvzhuang').append(item_dom);
                    }
                    else {
                        // 童装dom　show
                        $('.child_zone').show();
                        var child_item_dom = Create_item_dom(p_obj);
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

function Set_category_product(suffix){
    //通过分页获取分类商品数据，闭包实现
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
        var promoteUrl = GLConfig.baseApiUrl + suffix ;
        if (suffix.indexOf('?') > 0){
            promoteUrl = promoteUrl + 'page='+pageNum+'&page_size=10';
        }else{
            promoteUrl = promoteUrl + '?page='+pageNum+'&page_size=10';
        }
        var promoteCallBack = function (data) {
            $("#loading").hide();
            loading = false;
            pageNum += 1;
            nextPage = data.next;
            $.each(data.results,
                function(index,p_obj){
                    var item_dom = Create_item_dom(p_obj,false);
                    $('.glist').append(item_dom);
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

function Set_model_product(suffix){
    //获取同款式商品列表
    var promoteUrl = GLConfig.baseApiUrl + suffix;
    var promoteCallBack = function(data){
        $("#loading").hide();
        //设置女装推荐链接及图片
        $.each(data,
            function(index,p_obj){
                var item_dom = Create_item_dom(p_obj,true);
                $('.glist').append(item_dom);
            }
        );
        //设置时间及微信分享参数
        if (data && data.length > 0) {
            if (data[0].offshelf_time) {
                var shelf_time = new Date(data[0].offshelf_time.replace("T", " "));
                product_timer_new(shelf_time, data[0].is_saleopen);
            } else if (data[0].sale_time) {
                var shelf_time = new Date(data[0].sale_time);
                product_timer(shelf_time);
            }
        }
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
        success:promoteCallBack
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
    ss = checkTime(ss);

    if (!is_saleopen) {
        $(".top p").text("");
    } else if (ts >= 86400000) {
        $(".top p").text("剩余" + dd + "天" + hh + "时" + mm + "分");
        setTimeout(function () {
                product_timer_new(shelf_time, is_saleopen);
            },
            2000);
    } else if (ts < 86400000 && ts > 0) {
        $(".top p").text("剩余" + hh + "时" + mm + "分");
        setTimeout(function () {
                product_timer_new(shelf_time, is_saleopen);
            },
            2000);
    } else if (ts < 0) {
        $(".top p").text("已下架");
    }

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

Date.prototype.Format = function (fmt) {
    /*
     * 时间格式化
     * auther:yann
     * date:2015/22/8
     */
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
