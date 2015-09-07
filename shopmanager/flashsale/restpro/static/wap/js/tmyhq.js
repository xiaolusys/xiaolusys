/**
 * Created by linjie on 15-7-24.
 */
function create_yhqk_dom() {
    var html = $("#youhuiquan_kong").html();
    return hereDoc(html);
}

function create_yhq_dom(obj) {
    var xlmm_118 = $("#xlmm_118").html();
    return hereDoc(xlmm_118).template(obj)
}

function create_yhq_dom_used(obj) {
    var xlmm_118_used = $("#xlmm_118_used").html();
    return hereDoc(xlmm_118_used).template(obj)
}
function create_yhq_dom_post_fee(obj) {
    var xlmm_118_used = $("#post_fee").html();
    return hereDoc(xlmm_118_used).template(obj)
}
function create_yhq_dom_post_fee_used(obj) {
    var xlmm_118_used = $("#post_fee_used").html();
    return hereDoc(xlmm_118_used).template(obj)
}

$(document).ready(function () {
    var url = GLConfig.baseApiUrl + GLConfig.usercoupons;
    $.get(url, function (res) {
        console.log("new debug:", res);
        if (res.length > 0) {
            $.each(res, function (i, val) {
                //默认对象
                var yhq_obj = {"created": val.created, "deadline": val.deadline};

                if (val.coupon_value == 30 && val.status == 0 && val.coupon_type == 0) {
                    //满30返30  代理 coupon_type 4
                    var yhq_tree1 = create_yhq_dom(yhq_obj);
                    $(".youxiao").append(yhq_tree1);
                }
                if (val.coupon_value == 30 && val.poll_status == 2 && val.coupon_type == 0) {
                    //满30返30  代理 coupon_type 4 过期
                    var yhq_tree2 = create_yhq_dom(yhq_obj);
                    $(".youxiao").append(yhq_tree2);
                }
                if (val.coupon_value == 30 && val.status == 1 && val.coupon_type == 0) {
                    //满30返30  代理 coupon_type 4 已使用
                    var yhq_tree3 = create_yhq_dom_used(yhq_obj);
                    $(".youxiao").append(yhq_tree3);
                }
                if (val.coupon_value == 10 && val.status == 0 && val.coupon_type == 1) {
                    //10元现金券   coupon_type 5
                    var yhq_tree5 = create_yhq_dom_post_fee(yhq_obj);
                    $(".youxiao").append(yhq_tree5);
                }
                if (val.coupon_value == 10 && val.status == 1 && val.coupon_type == 1) {
                    //10元现金券   coupon_type 5 已使用
                    var yhq_tree6 = create_yhq_dom_post_fee_used(yhq_obj);
                    $(".youxiao").append(yhq_tree6);
                }
            });
        }
        else {
            var yhqk = create_yhqk_dom();
            $("body").append(yhqk);
        }

    });
});
