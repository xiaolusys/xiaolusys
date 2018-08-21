/**
 * Created by linjie on 15-7-22.
 */

function create_jf_dom(obj) {
    function jf_dom() {
        /*
         <li>
         <p class="time">最后修改时间：{{ modify }} </p>
         <div class="info"><div class="left"><img src=" {{ pic }}" /></div>
         <div class="right"><p>订单编号：<span class="caaaaaa">{{ oid }}</span></p>
         <p>订单金额：<span class="cf353a0">¥{{ value }}</span></p>
         <p>订单积分：<span class="cf353a0">{{ value }}</span></p></div></div></li>
         */
    };
    return hereDoc(jf_dom).template(obj)
}

function create_jfk_dom() {
    function jfk_dom() {
        /*
            <div class="kv"></div>
            <p class="tips">
                您还未获得积分，赶快去首页购买<br>商品，获取积分吧~
            </p>
            <a class="back-index" href="../index.html">去首页逛逛</a>
         */
    };
    return hereDoc(jfk_dom)
}


$(document).ready(function () {
    var url = "/rest/v1/user/integrallog/";
    $.get(url, function (res) {
        if (res.count > 0) {
            $.each(res.results, function (i, val) {
                var modify = (val.modified).replace('T', '  ');
                var value = val.log_value;
                var order = val.order_info;
                var pic = order.pic_link;
                if (pic == '') {
                    pic = "../images/icon-xiaolu.png";
                }
                var oid =order.order_id;
                var jf_obj = {"modify": modify, "value": value, "pic": pic, "oid": oid};
                var jf_dmtree = create_jf_dom(jf_obj);
                $(".jifen-list").append(jf_dmtree);
            });
        }
        else {
            var kong = create_jfk_dom();
            $("body").append(kong);
        }
    });

});

/**
 * Created by linjie on 15-7-23.
 */

function total_user_jifen() {
// 这个 接口可以获得与应授权用户的积分
    var url = "/rest/v1/user/integral/";
    $.get(url, function (res) {
        $.each(res.results, function (i, val) {
            var jifen_value = val.integral_value;
            //var content = '';
            //if (jifen_value != 0) {
            //    content = "您已经获得" + jifen_value + "个积分！"
            //} else {
            //    content = "您还未获得积分，赶快去首页购买<br>商品，获取积分吧~";
            //}
            //$(".tips").append(content);
        });
    });
}
