/**
 * Created by linjie on 15-7-22.
 */
console.log('hello world!');

var url = "/rest/v1/user/integrallog/";
$.get(url, function (res) {
	if(res.count>0){
    console.log(res);
    $.each(res.results, function (i, val) {
        var order = val.order;
        var modify = (val.modified).replace('T', '  ');
        var value = val.log_value;
        var pic = eval(order)[0].pic_link;
        if (pic == '') {
            pic = "https://www.baidu.com/img/bd_logo1.png";
        }
        var trade_id = eval(order)[0].trade_id;
        var oid = eval(order)[0].order_id;
        var li = '<li><p class="time">确认收货时间：' + modify + '</p>' +
            '<div class="info"><div class="left"><img src="' + pic + '" /></div>' +
            '<div class="right"><p>订单编号：<span class="caaaaaa">' + oid + '</span></p>' +
            '<p>订单金额：<span class="cf353a0">¥' + value + '</span></p>' +
            '<p>订单积分：<span class="cf353a0">' + value + '</span></p></div></div></li>';
        $(".jifen-list").append(li);
    });}
	else{
		//jump to integral is null page
		location.href = '/static/wap/pages/wodejifen-kong.html';
	}
});

