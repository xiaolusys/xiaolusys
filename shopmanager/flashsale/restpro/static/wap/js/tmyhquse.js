/**
 * Created by jishu_linjie on 8/17/15.
 */


function get_Coupon_On_Buy() {
    var url = "/rest/v1/user/mycoupon/";
    var nums = 0;//优惠券数量最小为０
    $.get(url, function (res) {
        console.log(res);
        if (res.length > 0) {
            //var nums = 0;
            $.each(res, function (i, val) {
                if (val.coupon_status == 3) {
                    nums = nums + 1;//有效可用的优惠券数量
                }
            });
            Coupon_Nums_Show(nums);//显示优惠券数量
        }
    });
}

function Coupon_Nums_Show(nums) {
    $("#coupon_nums").text("可用优惠券（" + nums + "）");
    if (nums > 0) {
        $("#coupon_nums").click(function () {
            console.log("jump to choose page...");
            location.href = "./choose-coupon.html";
        });
    }
    else if(nums==0){// 没有优惠券　　点击　领取优惠券
        $("#coupon_nums").text("可用优惠券（" + nums + "）");
        $("#coupon_value").text("点击领取");
        $("#coupon_value").click(function(){
            location.href = "./youhuiquan-kong.html";// 跳转到优惠券kong
        });
    }
}

//coupon_no: "YH15072955b89175ce412"
//coupon_status: 3
//coupon_type: 1
//coupon_user: "19"
//coupon_value: 3
//created: "2015-07-29"
//deadline: "2015-07-29 00:00"
//
//<ul class="coupons-list">
//            <li class="type1">
//                <p class="name">{{ coupon_name }}</p>
//
//                <p class="date">{{ created }} - {{ end }}</p>
//                <i class="icon-radio {{ coupon_class }}"></i>
//            </li>
//        </ul>


function get_Coupon_On_Choose() {
    var url = "/rest/v1/user/mycoupon/";
    $.get(url, function (res) {
        console.log(res);
        if (res.length > 0) {
            var nums = 0;
            $.each(res, function (i, val) {
                if (val.coupon_status == 3) {
                    nums = nums + 1;//有效可用的优惠券数量
                    var id = val.id;
                    var coupon_status = val.coupon_status;
                    var coupon_type = val.coupon_type;
                    var coupon_value = val.coupon_value;
                    var deadline = val.deadline.split(' ')[0];
                    var created = val.created;
                    var yhq_obj = {
                        "id":id,
                        "type": 1,
                        "full": 30,
                        "fan": 3,
                        "created": created,
                        "deadline": deadline,
                        "coupon_value": coupon_value
                    };
                    if (coupon_value == 3 && coupon_status == 3) {
                        //满30返3
                        var yhq_tree1 = Create_coupon_dom(yhq_obj);
                        $('.coupons').append(yhq_tree1);
                    }
                    if (coupon_value == 30 && coupon_status == 3) {
                        //满300返30
                        yhq_obj.type = 2;
                        yhq_obj.full = 300;
                        yhq_obj.fan = 30;
                        var yhq_tree2 = Create_coupon_dom(yhq_obj);
                        $('.coupons').append(yhq_tree2);
                    }
                }
            });
        }
    });
}

function Create_coupon_dom(obj) {
    var html = $("#coupon-template").html();
    return hereDoc(html).template(obj)
}

function choose_Coupon(coupon_id) {
    console.log(document.referrer);
    var buy_nuw_url = document.referrer.split("&")[0]+"&"+document.referrer.split("&")[1];
    var include_coupon = buy_nuw_url + "&coupon_id="+coupon_id;
    location.href = include_coupon;
}


function get_Coupon_Value_Show_In_Buy(){
    var coupon_id = getUrlParam("coupon_id");
    console.log("coupon_id:", coupon_id);
    var url = "/rest/v1/user/mycoupon/";
    $.get(url, function (res) {
        if (res.length > 0) {
            $.each(res, function (i, val) {
                if (val.coupon_status == 3 &&val.id==coupon_id) { //判断是否有效
                    console.log("coupon value end :",val.coupon_value);
                    //将显示出来的数值填充到页面中
                    var coupon_value = val.coupon_value;
                    $("#coupon_value").text("￥-"+coupon_value);
                }
            });
        }
    });
}

function getUrlParam(name) {
            var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)"); //构造一个含有目标参数的正则表达式对象
            var r = window.location.search.substr(1).match(reg);  //匹配目标参数
            if (r != null) return unescape(r[2]); return null; //返回参数值
        }