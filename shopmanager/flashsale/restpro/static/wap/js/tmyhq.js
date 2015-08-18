/**
 * Created by linjie on 15-7-24.
 */

//将从接口获取的JSON填充到HTML中

function create_yhq_dom(obj) {
    var deadline= obj.deadline.split(' ');
    obj.deadline = deadline[0];

    function yhq_dom() {
        /*
         <li class="type{{ type }}">
         <p class="name">全场任意商品满{{ full }}返{{ fan }}</p>
         <p class="date">{{ created }} － {{ deadline }}</p>
         </li>
         */
    };
    return hereDoc(yhq_dom).template(obj)
}


function create_yhqk_dom() {
    var html = $("#youhuiquan_kong").html();
    return hereDoc(html);
}

$(document).ready(function () {
    var url = GLConfig.baseApiUrl + GLConfig.user_own_coupon ;
    $.get(url, function (res) {
        if (res.length > 0) {
            $.each(res, function (i, val) {
                var coupon_status = val.coupon_status;
                var coupon_type = val.coupon_type;
                var coupon_value = val.coupon_value;
                var deadline = val.deadline;
                var created = val.created;
                //默认对象
                var yhq_obj = {"type": 1, "full": 30, "fan": 3, "created": created, "deadline": deadline};
                if (coupon_value == 3 && coupon_status == 3) {
                    //满30返3
                    var yhq_tree = create_yhq_dom(yhq_obj);
                    $(".youxiao").append(yhq_tree);
                }
                if (coupon_value == 30 && coupon_status == 3) {
                    //满300返30
                    yhq_obj.type = 2;
                    yhq_obj.full = 300;
                    yhq_obj.fan = 30;
                    var yhq_tree2 = create_yhq_dom(yhq_obj);
                    $(".youxiao").append(yhq_tree2);
                }
                if (coupon_value == 30 && coupon_status == 2) {
                    //已经过期的优惠券 满30返3
                    yhq_obj.type = 3;
                    yhq_obj.full = 300;
                    yhq_obj.fan = 30;
                    var yhq_tree3 = create_yhq_dom(yhq_obj);
                    $(".shixiao_list").append(yhq_tree3);
                }
                if (coupon_value == 3 && coupon_status == 2) {
                    //已经过期的优惠券
                    yhq_obj.type = 4;
                    yhq_obj.full = 30;
                    yhq_obj.fan = 3;
                    var yhq_tree4 = create_yhq_dom(yhq_obj);
                    $(".shixiao_list").append(yhq_tree4);
                }
            });
        }
        else {
            var yhqk = create_yhqk_dom();
            $("body").append(yhqk);
        }

    });
});
