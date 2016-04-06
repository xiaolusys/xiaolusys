$(document).ready(function() {
	getQsType();
	QuestOnclick();
});
var getQsType = function() {
	$.ajax({
		type: 'GET',
		url: 'http://192.168.1.31:9000/rest/v1/faqs/get_types',
		success: function(result) {
			//TODO
			var ul = $('ul');
			var h = [];
			result.forEach(function(value) {
				h.push(createLi(value));
			});
			ul.append(h.join(''));
		}
	});
}
var createLi = function(Qs) {
	var h = [];
	h.push('<li>');
	h.push('<div id="order-question">');
	h.push('<img src="">');
	h.push('<p>订单问题</p>');
	h.push('</div>');
	h.push('<div class="row-col display-hide">');
	h.push('<div class="row" style="border-bottom: 1px solid #ffffff">');
	h.push('<div class="col" style="border-right: 1px solid #ffffff"><a href="logisticsQ.html">物流配送</a></div>');
	h.push('<div class="col">售后咨询</div>');
	h.push('</div>');
	h.push('<div class="row">');
	h.push('<div class="col" style="border-right: 1px solid #ffffff">退货问题</div>');
	h.push('<div class="col">退款问题</div>');
	h.push('</div>');
	h.push('</div>');
	h.push('</li>');
	// <li>
	// 	<div id="order-question">
	// 		<img src="">
	// 		<p>订单问题</p>
	// 	</div>
	// 	<div class="row-col display-hide">
	// 		<div class="row" style="border-bottom: 1px solid #ffffff">
	// 			<div class="col" style="border-right: 1px solid #ffffff"><a href="logisticsQ.html">物流配送</a></div>
	// 			<div class="col">售后咨询</div>
	// 		</div>
	// 		<div class="row">
	// 			<div class="col" style="border-right: 1px solid #ffffff">退货问题</div>
	// 			<div class="col">退款问题</div>
	// 		</div>
	// 	</div>
	// </li>
	return h.join('');

};

var QuestOnclick = function() {
	var $orderQ = $('li div[id="order-question"]');
	var $detailQ = $orderQ.next();
	$orderQ.bind('click', function(e) {
		if ($detailQ.hasClass('display-hide')) {
			$detailQ.removeClass('display-hide');
		} else {
			$detailQ.addClass('display-hide');
		}
	});
};