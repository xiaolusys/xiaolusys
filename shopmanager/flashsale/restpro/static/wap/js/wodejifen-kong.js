/**
 * Created by linjie on 15-7-23.
 */
console.log('wodejifen-kong js is ok');

var url = "/rest/v1/user/integral/";
$.get(url, function (res) {
    $.each(res.results, function (i, val) {
        var jifen_value = val.integral_value;
        console.log(jifen_value);
        //var content = '';
        //if (jifen_value != 0) {
        //    content = "您已经获得" + jifen_value + "个积分！"
        //} else {
        //    content = "您还未获得积分，赶快去首页购买<br>商品，获取积分吧~";
        //}
        //$(".tips").append(content);
    });
});



