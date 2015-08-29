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

$(document).ready(function () {
    var url = GLConfig.baseApiUrl + GLConfig.user_own_coupon;
    $.get(url, function (res) {
        if (res.length > 0) {
            $.each(res, function (i, val) {
                var coupon_status = val.coupon_status;
                var coupon_type = val.coupon_type;
                var coupon_value = val.coupon_value;
                var deadline = val.deadline;
                var created = val.created;
                //默认对象
                console.log("devug val:", val);// status 0:已领取 1:已使用  2:已过期
                var yhq_obj = {"type": 2, "full": 30, "fan": 30, "created": created, "deadline": deadline};
                if (coupon_value == 30 && coupon_status == 0 && coupon_type == 4) {
                    //满30返30  代理 coupon_type 4
                    var yhq_tree1 = create_yhq_dom(yhq_obj);
                    $(".youxiao").append(yhq_tree1);
                }
                if (coupon_value == 30 && coupon_status == 2 && coupon_type == 4) {
                    //满30返30  代理 coupon_type 4 过期
                    yhq_obj.type = 4;
                    var yhq_tree2 = create_yhq_dom(yhq_obj);
                    $(".youxiao").append(yhq_tree2);
                }
                if (coupon_value == 30 && coupon_status == 1 && coupon_type == 4) {
                    //满30返30  代理 coupon_type 4 已使用
                    yhq_obj.type = 2;
                    var yhq_tree3 = create_yhq_dom_used(yhq_obj);
                    $(".youxiao").append(yhq_tree3);
                }
            });
        }
        else {
            var yhqk = create_yhqk_dom();
            $("body").append(yhqk);
        }

    });
});
