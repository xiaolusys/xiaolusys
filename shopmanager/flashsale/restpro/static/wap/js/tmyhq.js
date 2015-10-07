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
    var RELEASE = 1;
    var PAST = 2;
    var USED = 1;
    var UNUSED = 0;

    var url = GLConfig.baseApiUrl + GLConfig.usercoupons;
    $.get(url, function (res) {
        console.log("new debug:", res);
        if (res.length > 0) {
            $.each(res, function (i, val) {
                //默认对象
                if (val.status == UNUSED && val.poll_status == RELEASE) {//未使用　并且　券池状态为发放状态
                    var yhq_tree7 = create_valid(val);
                    $(".youxiao").append(yhq_tree7);
                }
                else if (val.poll_status == PAST) {// 券池状态为过期状态
                    var yhq_tree9 = create_past(val);
                    $(".shixiao_list").append(yhq_tree9);
                }
                else if (val.poll_status == RELEASE && val.status == USED) { //发放状态的优惠券并且已经使用过
                    var yhq_tree8 = create_not_valid(val);
                    $(".shixiao_list").append(yhq_tree8);
                }
            });
        }
        else {
            var yhqk = create_yhqk_dom();
            $("body").append(yhqk);
        }

    });
});
