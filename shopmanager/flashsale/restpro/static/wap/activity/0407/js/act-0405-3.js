$(document).ready(function() {
	var baseurl = 'http://staging.xiaolumeimei.com';
	// var baseurl = 'http://192.168.10.74:8000';
	var $top = $('.act-0405-3-top')[0];
	var screenWidth = document.body.clientWidth;
	$top.style.height = screenWidth * 1.28 + 'px';
	//倒计时
	var timer = function(intDiff) {
		window.setInterval(function() {
			var day = 0,
				hour = 0,
				minute = 0,
				second = 0;

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
	};

	//请求初始数据
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
			}
		});
		$.ajax({
			type: 'GET',
			url: baseurl + '/sale/promotion/main/3/',
			success: function(resp) {
				//add cards
				var h = [];
				h.push('<div class="act-cards-container">');
				for (var i = 1; i < 10; i++) {
					h.push('<div class="col-xs-4 no-padding act-card">');
					if (resp.cards[i] == 1) {
						h.push('<img src="../img/card_' + i + '.png" class="card_' + i + '">');
					} else {
						h.push('<img src="../img/card_' + i + '.png" class="card_' + i + ' card-hide">');
					}
					h.push('</div>');
				}
				h.push('</div>');
				$('.act-0405-3-time').after(h.join(''));

				//add envelopes
				h = [];
				h.push('<div class="act-0405-3-envelopes"><p>' + resp.envelopes.length + '</p></div>');
				h.push('<div class="act-evelops-container">');
				resp.envelopes.forEach(function(envelope) {
					h.push('<div class="col-xs-2 no-padding text-center act-evelops">');
					if (envelope.status === 'open' && envelope.type === 'card') {
						h.push('<img class="act-icon act-evelop" src="../img/act-0405-26.png" data-id = "' + envelope.id + '"/>');
						h.push('<p>拼图</p>');
					} else if (envelope.status === 'open' && envelope.type === 'cash') {
						h.push('<img class="act-icon act-evelop" src="../img/act-0405-25.png" data-id = "' + envelope.id + '"/>');
						h.push('<p>红包</p>');
					} else {
						h.push('<img class="act-icon act-evelop" src="../img/act-0405-27.png" data-id = "' + envelope.id + '"/>');
						h.push('<p>未拆开</p>');
					}
					h.push('</div>');
				});
				h.push('</div');
				$('.act-0405-3-invite').after(h.join(''));

				//add envelopes of inactives
				h = [];
				resp.inactives.forEach(function(inactive) {
					h.push('<div class="col-xs-2 no-padding text-center act-evelops">');
					h.push('<img class="act-icon act-inactive" src="' + inactive.headimgurl + '" />');
					h.push('<p>未激活</p>');
					h.push('</div>');
				});
				$('.act-evelops-container').after(h.join(''));

				//add  sleepbags records
				h = [];
				h.push('<div class="act-0405-3-sleepbags"><p>' + resp.award_left + '</p></div>');
				h.push('<div class="act-sleepbags-container">');
				resp.award_list.forEach(function(award) {
					h.push('<div class="col-xs-10 no-padding text-left act-0405-3-sleepbags-record">');
					h.push('<p>' + award.customer_nick + ',打开第' + award.invite_num + '个信封，获得最后一张“拼”图，成功拼成一个睡袋</p>');
					h.push('</div>');
				});
				h.push('</div>');
				$('.act-0405-env-show').after(h.join(''));
			}
		});
	};
	//打开信封
	var openEnvelope = function(event) {
		var envelope_id, $eventTarget;
		$eventTarget = $(event.target);
		envelope_id = $eventTarget.attr('data-id');
		$.ajax({
			type: 'GET',
			url: baseurl + '/sale/promotion/open_envelope/' + envelope_id + '/',
			success: function(resp) {
				var h = [];
				h.push('<div class="act-popup" >');
				h.push('<img src="' + resp.friend_img + '" class="act-customer-img"/>');
				h.push('<p>成功邀请 ' + resp.friend_nick + ' </p>');
				if (resp.type == 'card') {
					h.push('<img src="../img/cardGet_' + resp.value + '.png" class="act-card-get"/>');
				} else {
					h.push('<div class="act-get">');
					h.push('<p>' + resp.yuan_value + '</p>');
					h.push('</div>');
					h.push('');
					h.push('<img src="../img/cash_bg.png" class="act-card-get"/>');
				}

				h.push('</div>');
				$('body').append(h.join(''));
				//show card
				if (resp.type == 'card' && resp.status == 'close') {
					var $img = $('.card_' + resp.value);
					$img.removeClass('car_hide');
				}
				//change envelop status
				var $openedImg = $('img[data-id=' + resp.id + ']')[0];
				if (resp.type == 'card') {
					$openedImg.src = '../img/act-0405-26.png';
				} else if (resp.type == 'cash') {
					$openedImg.src = '../img/cash_bg.png';
				}
			},
			error: function(resp) {}
		});

	};
	//dropdown popup
	var closePopup = function() {
		var $popup = $('.act-popup');
		$popup.remove();
		var hideLength = $('.act-cards-container .card-hide').length;
		if (hideLength == 8) {
			var h = [];
			h.push('<div class="act-popup" >');
			h.push('<img src="../img/act-0405-37.png" class="complete-cards"/>');
			h.push('</div>');
			$('body').append(h.join(''));
		}
	};
	var setupWebViewJavascriptBridge = function(callback) {
		if (window.WebViewJavascriptBridge) {
			return callback(WebViewJavascriptBridge);
		}
		if (window.WVJBCallbacks) {
			return window.WVJBCallbacks.push(callback);
		}
		window.WVJBCallbacks = [callback];
		var WVJBIframe = document.createElement('iframe');
		WVJBIframe.style.display = 'none';
		WVJBIframe.src = 'wvjbscheme://__BRIDGE_LOADED__';
		document.documentElement.appendChild(WVJBIframe);
		setTimeout(function() {
			document.documentElement.removeChild(WVJBIframe)
		}, 0)
	};
	var OSTest = function() { // 客户端平台检测　返回
		var u = navigator.userAgent;
		var isAndroid = u.indexOf('Android') > -1 || u.indexOf('Adr') > -1; //android终端
		var isiOS = !!u.match(/\(i[^;]+;( U;)? CPU.+Mac OS X/); //ios终端
		if (isAndroid == true) {
			return 'Android';
		} else if (isiOS == true) {
			return 'iOS';
		} else {
			return 'web'
		}
	};

	requestData();
	$(document).on('click', '.act-evelops-container .act-evelop', openEnvelope);
	$(document).on('click', '.act-card-get', closePopup);
	$(document).on('click', '.act-get', closePopup);
	$(document).on('click', '.complete-cards', function() {
		$('.act-popup').remove();
		$('.act-cards-container').remove();
		var h = [];
		h.push('<img src="../img/act-0405-20.png" class="complete-get">');
		$('.act-0405-3-time').after(h.join(''));
	});
	$(document).on('click', '.act-0405-3-invite img', function() {
		var os = OSTest();
		console.log('os share:', os)
		if (os == 'iOS') {
			setupWebViewJavascriptBridge(function(bridge) {
				var data = {
					'share_to': '',
					'active_id': '1'
				};
				bridge.callHandler('callNativeShareFunc', data, function(response) {
					console.log("callNativeShareFunc called with:", data);
				});
			})
		} else {
			if (window.AndroidBridge) {
				var data = {
					'share_to': '',
					'active_id': '1'
				};
				window.AndroidBridge.callNativeShareFunc(data.share_to, data.active_id);
			}
		}
	});
});