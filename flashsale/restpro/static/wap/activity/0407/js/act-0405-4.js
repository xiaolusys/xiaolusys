$(document).ready(function() {
	var baseurl = 'http://staging.xiaolumeimei.com';
	// var baseurl = 'http://192.168.10.74:8000';
	var $top = $('.act-0405-4-top')[0];
	var screenWidth = document.body.clientWidth;
	$top.style.height = screenWidth * 1.28 + 'px';

	var requestData = function() {
		$.ajax({
			type: 'GET',
			url: baseurl + '/sale/promotion/stats/3/',
			success: function(resp) {
				var h = [];
				h.push('<div class="act-0405-4-text">');
				h.push('<p>通过您的邀请，为小鹿美美带来了36位好友</p>');
				h.push('<p>您完成了拼图，获得了浴巾</p>');
				h.push('</div>');
				$('.act-0405-4-end').after(h.join(''));

				h = [];
        		h.push('<div class="act-0405-4-packet">');
        		h.push('<p>88.88</p>');
        		h.push('</div>');
        		$('.act-0405-4-top').after(h.join(''));
			}
		});
	};
	requestData();
});