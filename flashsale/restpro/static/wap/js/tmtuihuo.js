/**
 * Created by jishu_linjie on 8/20/15.
 */

function Create_tuihuo_dom(obj) {
    var html = $("#tuihuo_list").html();
    return hereDoc(html).template(obj)
}

function create_thk_dom() {
    var html = $("#tuihuo_kong").html();
    return hereDoc(html)
}

$(document).ready(function () {
    Set_refund_detail();
    $(window).scroll(function () {
        loadData();// 更具页面下拉情况来加载数据
    });
});
var pageNumber = 1;
function Set_refund_detail() {
    //请求URL 获取用户的所有退款单
    var requestUrl = GLConfig.baseApiUrl + GLConfig.refunds + "?page=" + pageNumber;
    //请求成功回调函数
    var requestCallBack = function (data) {
        console.log("共", data.count, '条');
        $.each(data.results, function (index, ref) {
            // 获取产品图片
            var detail_dom = Create_tuihuo_dom(ref);
            $('.jifen-list').append(detail_dom);
        });
        pageNumber += 1;
    };
    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {},
        dataType: 'json',
        success: requestCallBack,
        error: function (data) {
            if (data.status == 403) {
                window.location = GLConfig.login_url + '?next=' + "/static/wap/pages/wodetuihuo.html";
            }
            else if (data.status == 404) {
                drawToast("已经到最底了哟~");
            }
        }
    });
}

function loadData() {//动态加载数据
    var totalheight = parseFloat($(window).height()) + parseFloat($(window).scrollTop());//浏览器的高度加上滚动条的高度
    if ($(document).height() - 5 <= totalheight)//当文档的高度小于或者等于总的高度的时候，开始动态加载数据
    {
        Set_refund_detail();
    }
}