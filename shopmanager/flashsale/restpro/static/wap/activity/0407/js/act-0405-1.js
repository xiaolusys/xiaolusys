$(document).ready(function() {
	var $addImg = $('.act-0405-add img');
	var $addBkg = $('.act-0405-add');
	var baseurl = 'http://staging.xiaolumeimei.com';
	//倒计时
	var timer = function(intDiff) {
			window.setInterval(function() {
				var day = 00,
					hour = 00,
					minute = 00,
					second = 00;

				//时间默认值		
				if (intDiff > 0) {
					day = Math.floor(intDiff / (60 * 60 * 24));
					hour = Math.floor(intDiff / (60 * 60)) - (day * 24);
					minute = Math.floor(intDiff / 60) - (day * 24 * 60) - (hour * 60);
					second = Math.floor(intDiff) - (day * 24 * 60 * 60) - (hour * 60 * 60) - (minute * 60);
				}
				if (day <= 9) day = '0' + day;
				if (hour <= 9) hour = '0' + hour;
				if (minute <= 9) minute = '0' + minute;
				if (second <= 9) second = '0' + second;
				$('#day_show').html(day);
				$('#hour_show').html(hour);
				$('#minute_show').html(minute);
				$('#second_show').html(second);
				intDiff--;
			}, 1000);
		}
		//add activity
	var add = function() {
		var $addImg = $('.act-0405-add img');
		var celNum = $('input').val();
		if ($addImg.hasClass('act-0405-add-img')) {
			$addImg.removeClass('act-0405-add-img').addClass('act-0405-added-img');
			$.ajax({
				data: {
					'mobile': celNum
				},
				type: 'post',
				url: baseurl + '/sale/promotion/apply/3/',
				success: function(res) {
					if (res.rcode == 0) {
						if (res.next == 'download') {
							window.location.href = '../html/act-0405-2.html';
						} else if (res.next == 'mainpage') {
							window.location.href = '../html/act-0405-3.html';
						} else if (res.next == 'snsauth') {
							window.location.href = '/sale/promotion/weixin_snsauth_join/3/';
						} else if (res.next == 'activate') {
							window.location.href = '/sale/promotion/activate/3/';
						}

					} else {
						$addImg.removeClass('act-0405-added-img').addClass('act-0405-add-img');
						$('input').val('');
						$('input')[0]['placeholder'] = '请重新输入';
					}
				}
			});
		}
	};

	var requestData = function() {
		var end_time, current_time, rest_time;
		$.ajax({
			type: 'GET',
			url: baseurl + '/sale/promotion/apply/3/',
			success: function(res) {
				//set rest time of activity
				end_time = res.end_time;
				current_time = (new Date()).getTime();
				rest_time = parseInt((end_time - current_time) / 1000);
				timer(rest_time);
				//cellNumber input
				var $cellNum = $('.act-0405-celNumber');
				if (res.mobile_required && $cellNum.hasClass('act-0405-hide')) {
					$cellNum.removeClass('act-0405-hide');
				}
				//show customer img
				var h = [];
				h.push('<img src="' + res.img + '">');
				h.push('<div class="act-0405-beInvited－text">');
				h.push('有福同享！我在集拼图换浴巾，送你一片拼图，快来一起加入吧～');
				h.push('</div>');
				$('.act-0405-beInvited').append(h.join(''));
			},
			error: function(res) {
				$('input')[0]['placeholder'] = '请重新输入';
			}
		});
	};
	requestData();
	$(document).on('click', '.act-0405-add img', add);
	$(document).on('click', '.act-0405-add', add);
});