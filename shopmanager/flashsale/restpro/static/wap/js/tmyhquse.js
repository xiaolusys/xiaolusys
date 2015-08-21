/**
 * Created by jishu_linjie on 8/17/15.
 */


function get_Coupon_On_Buy() {
    var url = GLConfig.baseApiUrl + GLConfig.user_own_coupon ;

    $.get(url, function (res) {
        if (res.length > 0) {
            var nums = 0;
            $.each(res, function (i, val) {
                if (val.coupon_status == 3) {
                    nums = nums + 1;//有效可用的优惠券数量
                }
            });
            if(nums==0){
                Coupon_Nums_Show(-1);// 表示曾经有过期或这使用过的优惠券
            }
            else{
                    Coupon_Nums_Show(nums);//显示优惠券数量
                }
        }
        else if(res.length==0){
            Coupon_Nums_Show(0);//显示优惠券数量
        }
    });
}

function Coupon_Nums_Show(nums) {
    console.log('nums nums ',nums);
    $("#coupon_nums").text("可用优惠券（" + nums + "）");
    if (nums > 0) {
        $("#coupon_nums").click(function () {
            console.log("jump to choose page...");
            location.href = "./choose-coupon.html";
        });
    }
    // 用户创建自己的优惠券　　满三十　即可达到创建条件　关闭本功能　
    //else if (nums == 0) {// 没有优惠券　　点击　领取优惠券
    //    $("#coupon_nums").text("可用优惠券（" + nums + "）");
    //    $("#coupon_value").text("点击领取");
    //    $("#coupon_value").click(function () {
    //        //　或者这里直接生成创建优惠券
    //        //　判断页面的订单价格生成　对应的　优惠券　类型　价值
    //        var coupon_type = 1;// 优惠券类型 这里可以根据页面　数据判断生成那种类型的优惠券
    //        var requestUrl = GLConfig.baseApiUrl + GLConfig.create_user_pay_coupon; // 用户在支付页面创建自己的优惠券
    //        //　１:满３０　减3  2:满３００减３０  3: 待定
    //        var total_money = parseFloat($("#total_money").html().split(">")[2]);
    //        if (total_money >= 30) {
    //            console.log(total_money);
    //
    //            $.ajax({
    //                type: 'post',
    //                url: requestUrl,
    //                data: {'csrfmiddlewaretoken': csrftoken, 'coupon_type': coupon_type},
    //                dataType: 'json',
    //                success: requestCallBack
    //            });
    //            function requestCallBack(res) {
    //                console.log(res);
    //                if(res[0]=='ok'){
    //                location.href = "./choose-coupon.html";
    //                }
    //                else{
    //                    console.log("用户创建优惠券失败！！！");
    //                }
    //            }
    //        }
    //        else{
    //            drawToast("您的订单不满３０元哦~");
    //        }
    //    });
    //}
    else if (nums == 0) {
        $("#coupon_nums").text("可用优惠券（" + 0 + "）");
        $("#coupon_value").text("点击领取");
        $("#coupon_value").click(function () {
            location.href = "./youhuiquan-kong.html"; //跳转到优惠券空页面
        });
    }

    else if(nums==-1){
        $("#coupon_nums").text("可用优惠券（" + 0 + "）");
        $("#coupon_value").text("点击领取");
        $("#coupon_value").click(function (){
            location.href = "./youhuiquan-kong.html"; //跳转到优惠券空页面
        });
    }
}


function get_Coupon_On_Choose() {
     var url = GLConfig.baseApiUrl + GLConfig.user_own_coupon ;
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
                        "id": id,
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
                    if (coupon_value == 50 && coupon_status == 3) {
                        //满300返30
                        yhq_obj.type = 5;
                        yhq_obj.full = 300;
                        yhq_obj.fan = 30;
                        var yhq_tree3 = Create_coupon_dom(yhq_obj);
                        $('.coupons').append(yhq_tree3);
                    }

                    if(nums==0){
                        pop_info();
                    }
                }
            });
        }
        else {
            // 显示提示信息　没有优惠券
            pop_info();
        }
    });
}

function Create_coupon_dom(obj) {
    if(obj.type==5){
        var html = $("#coupon_template_xlmm_coupon").html();
    }
    else{
        var html = $("#coupon-template").html();
    }
    return hereDoc(html).template(obj)
}

function choose_Coupon(coupon_id) {
    swal({
            title: "",
            text: '确定选择这张优惠券吗？',
            type: "",
            showCancelButton: true,
            imageUrl: "http://image.xiaolu.so/logo.png",
            confirmButtonColor: '#DD6B55',
            confirmButtonText: "确定",
            cancelButtonText: "取消"
        },
        function () {//确定　则跳转
            console.log(document.referrer);
            var buy_nuw_url = document.referrer.split("&")[0] + "&" + document.referrer.split("&")[1];
            var include_coupon = buy_nuw_url + "&coupon_id=" + coupon_id;
            location.href = include_coupon;
        });
}

function change_Coupon_Stauts(coupon_id){
    console.log(coupon_id);
    // 使用过的优惠劵　修改其状态到　使用过的状态
    var requestUrl = GLConfig.baseApiUrl + GLConfig.change_user_coupon_used.template({"coupon_id":coupon_id});
    console.log(requestUrl);
    $.ajax({
        type: 'post',
        url: requestUrl,
        data: {'csrfmiddlewaretoken': csrftoken, 'pk': coupon_id},
        dataType: 'json',
        success: requestCallBack
    });
    function requestCallBack(res) {
        if (res[0] == 'ok') {
            console.log("用户优惠券状态修改成功！！！");
        }
        else if(res[0] == "notInStatus"){
            drawToast("不可用优惠券！");
        }
        else {
            console.log("用户优惠券修改失败！！！");
        }
    }
}

function get_Coupon_Value_Show_In_Buy() {
    var coupon_id = getUrlParam("coupon_id");
    console.log("coupon_id:", coupon_id);
    var url = GLConfig.baseApiUrl + GLConfig.get_user_coupon_by_id.template({"coupon_id": coupon_id});
    console.log(url);
    $.get(url, function (res) {
        console.log(res);
        console.log(res[0],'res');
        if (res.length > 0) {
            if (res[0].coupon_status == 3 && res[0].id == coupon_id) { //判断是否有效
                console.log("coupon value end :", res[0].coupon_value);
                //将显示出来的数值填充到页面中
                var coupon_value = res[0].coupon_value;
                var total_money = parseFloat($("#total_money").html().split("¥")[1]);
                if (total_money > 30 && res[0].coupon_type == 4) {// 大于30才能使用 并且优惠券类型是4  代理专享优惠券
                    $("#coupon_value").text("¥-" + coupon_value);
                }
                else if (total_money < 30 && res[0].coupon_type == 4) {
                    drawToast("优惠券不可用哦~");
                }
                else {
                    drawToast("优惠券不可用哦~");
                }
            }
        }
    });
}

function getUrlParam(name) {
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)"); //构造一个含有目标参数的正则表达式对象
    var r = window.location.search.substr(1).match(reg);  //匹配目标参数
    if (r != null) return unescape(r[2]);
    return null; //返回参数值
}

function pop_info() {
    // 显示提示信息　没有优惠券
    swal({
            title: "",
            text: '您暂时还没有优惠券哦~',
            type: "",
            showCancelButton: false,
            imageUrl: "http://image.xiaolu.so/logo.png",
            confirmButtonColor: '#DD6B55',
            confirmButtonText: "返回",
            cancelButtonText: "取消"
        },
        function () {//确定　则跳转
            location.href = document.referrer;
        });
}