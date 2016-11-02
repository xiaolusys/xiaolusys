/**
 * Created by jishu_linjie on 10/19/15.
 */
/**
 * Created by jishu_linjie on 10/17/15.
 */

function Create_Nvzhuang_Dom(obj) {
    var html = $("#nvzhuang_li").html();
    return hereDoc(html).template(obj);
}

var pageNumber = 1;

function getSaleProduct() {
    var saleprourl = GLConfig.baseApiUrl + GLConfig.hot_product + "?page=" + pageNumber;
    $.ajax({
        type: 'get',
        url: saleprourl,
        data: {},
        dataType: 'json',
        success: refundCallBack,
        error: function (data) {
            if (data.status == 403) {
                window.location = GLConfig.login_url + '?next=' + "/static/wap/pages/hot_product_praise.html";
            }
            else if (data.status == 404){
                drawToast("已经到最底了哟~");
            }
        }
    });
    function refundCallBack(res) {
        setSaleProduct(res);
        pageNumber += 1;
        console.log("pageNumber: ", pageNumber);
    }
}

function setSaleProduct(res) {
    console.log("共", res.count, "个产品");
    console.log("下一页：", res.next);
    console.log("上一页：", res.previous);
    console.log("当前页数据：", res.results);
    var sale_pros = res.results;
    //如果没有产品　提示跳转到　主页
    if (res.count == 0) {
        swal({
                title: "",
                text: '暂无投票产品,去首页看看~',
                type: "",
                showCancelButton: false,
                imageUrl: "http://img.xiaolumeimei.com/logo.png",
                confirmButtonColor: '#DD6B55',
                confirmButtonText: "确定",
                cancelButtonText: ""
            },
            function () {//确定　则跳转
                var include_coupon = '/static/wap/index.html';
                location.href = include_coupon;
            });
    }
    $(sale_pros).each(function (index, pro) {
        var dom = Create_Nvzhuang_Dom(pro);
        $("#list").append(dom);
    });
    // 绑定点赞事件
    praiseClick();
}

// 点赞事件触发
function praiseClick() {
    $(".love_icon").click(function () {
        var dom = $(this);
        var id = dom.attr('id');
        console.log("id:", id);
        var data = {"id": id, 'csrfmiddlewaretoken': csrftoken};
        changeHotVal(data, dom);
    });

}

function changeHotVal(data, dom) {
    var id = data.id;
    var hotUrl = GLConfig.baseApiUrl + GLConfig.change_hot_pro_hot_val.template({"id": id});
    console.log("hotUrl: ", hotUrl);
    $.ajax({
        type: 'post',
        url: hotUrl,
        data: data,
        dataType: 'json',
        success: refundCallBack
    });
    function refundCallBack(res) {
        console.log("res: ", res);
        if (res.today_count < 1) {
            drawToast("感谢您的点赞！" + "目前已经有" + res.hot_val + "人点赞，感谢您的参与！");
        }
        $(dom).addClass("praise");
        if (res.today_count >= 1) {
            drawToast("您已经超过了1次点赞了，太感谢您了！")
        }
        console.log("dom", dom);
        $(dom.parent().children()[1]).html('+' + res.hot_val);
    }
}


function loadData() {//动态加载数据
    var totalheight = parseFloat($(window).height()) + parseFloat($(window).scrollTop());//浏览器的高度加上滚动条的高度
    if ($(document).height() - 5 <= totalheight)//当文档的高度小于或者等于总的高度的时候，开始动态加载数据
    {
        //加载数据
        console.log("must loading the more data !");
        getSaleProduct();

    }
}

