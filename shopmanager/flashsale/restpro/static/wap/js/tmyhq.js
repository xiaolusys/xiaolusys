/**
 * Created by linjie on 15-7-24.
 */
function create_yhqk_dom() {
    var html = $("#youhuiquan_kong").html();
    return hereDoc(html);
}
function create_valid(obj){
    var c_valid = $("#c_valid").html();
    return hereDoc(c_valid).template(obj)
}
function create_not_valid(obj){
    var c_not_valid = $("#c_not_valid").html();
    return hereDoc(c_not_valid).template(obj)
}

$(document).ready(function () {
    var url = GLConfig.baseApiUrl + GLConfig.usercoupons;
    $.get(url, function (res) {
        console.log("new debug:", res);
        if (res.length > 0) {
            $.each(res, function (i, val) {
                //默认对象
                if (val.status == 0) {
                    var yhq_tree7 = create_valid(val);
                    $(".youxiao").append(yhq_tree7);
                }
                if (val.status == 1) {
                    var yhq_tree8 = create_not_valid(val);
                    $(".youxiao").append(yhq_tree8);
                }
            });
        }
        else {
            var yhqk = create_yhqk_dom();
            $("body").append(yhqk);
        }

    });
});
