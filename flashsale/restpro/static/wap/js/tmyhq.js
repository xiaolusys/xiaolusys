/**
 * Created by linjie on 15-7-24.
 */
function create_yhqk_dom() {
    var html = $("#youhuiquan_kong").html();
    return hereDoc(html);
}
function create_valid(obj) {
    var c_valid = $("#c_valid").html();
    return hereDoc(c_valid).template(obj)
}
function create_not_valid(obj) {
    var c_not_valid = $("#c_not_valid").html();
    return hereDoc(c_not_valid).template(obj)
}

function create_past(obj) {
    var c_past = $("#c_past").html();
    return hereDoc(c_past).template(obj)
}

$(document).ready(function () {
    set_coupon();
    $(window).scroll(function () {
        loadData(set_coupon);// 更具页面下拉情况来加载数据
    });
    set_past_coupon();
});

var pageNumber = 1;

function set_coupon() {
    var RELEASE = 1;
    var USED = 1;
    var UNUSED = 0;
    var url = GLConfig.baseApiUrl + GLConfig.usercoupons + "?page=" + pageNumber;
    $.ajax({
        "url": url,
        "type": "get",
        "success": callback,
        "csrfmiddlewaretoken": csrftoken,
        error: function (data) {
            console.log('debug profile:', data);
            if (data.status == 403) {
                //drawToast('您还没有登陆哦!');
                location.href = "denglu.html";
            }
        }
    });

    function callback(res) {
        $.each(res.results, function (i, val) {
            //默认对象
            if (val.status == UNUSED && val.poll_status == RELEASE) {//未使用　并且　券池状态为发放状态
                var yhq_tree7 = create_valid(val);
                $(".youxiao").append(yhq_tree7);
            }
            else if (val.poll_status == RELEASE && val.status == USED) { //发放状态的优惠券并且已经使用过
                var yhq_tree8 = create_not_valid(val);
                $(".shixiao_list").append(yhq_tree8);
            }
        });
        pageNumber += 1;
    }
}

function set_past_coupon() {
    var PAST = 2;
    var pasturl = GLConfig.baseApiUrl + GLConfig.past_usercoupons;// 过期
    $.get(pasturl, function (past) {
        console.log("user_past_coupon:", past);
        $.each(past.results, function (i, val) {
            //默认对象
            if (val.poll_status == PAST) {// 券池状态为过期状态
                var yhq_tree9 = create_past(val);
                $(".shixiao_list").append(yhq_tree9);
            }
        });
    });
}

function loadData(func) {//动态加载数据
    var totalheight = parseFloat($(window).height()) + parseFloat($(window).scrollTop());//浏览器的高度加上滚动条的高度
    if ($(document).height() - 5 <= totalheight)//当文档的高度小于或者等于总的高度的时候，开始动态加载数据
    {
        func();
    }
}