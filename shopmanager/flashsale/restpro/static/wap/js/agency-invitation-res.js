/**
 * Created by jishu_linjie on 4/1/16.
 */

var nextReferalPage = GLConfig.agency_invitation_res;

var detector = {
  test: function(ua) {
    return navigator.userAgent.indexOf(ua) >= 0;
  },

  isAndroid: function() {
    return this.test('Android');
  },

  isIOS: function() {
    return this.test('iPhone') || this.test('iPad') || this.test('iPod');
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
  setTimeout(function() { document.documentElement.removeChild(WVJBIframe); }, 0);
};


var testClickCount = 0;
$(document).ready(function() {
  getMamaInvitationRes();
  $(window).scroll(function() {
    loadData(getMamaInvitationRes); // 更具页面下拉情况来加载数据
  });
  getMamaFuturn();
  var a = window.screen.height;
  var b = window.screen.width;
  $(".js-invite").click(function() {
    var data = { 'share_to': '', 'active_id': '4' };
    if (detector.isIOS()) {
      setupWebViewJavascriptBridge(function(bridge) {
        bridge.callHandler('callNativeShareFunc', data, null);
      });
    } else if (detector.isAndroid() && window.AndroidBridge) {
      window.AndroidBridge.callNativeShareFunc(data.share_to, data.active_id);
    }
  });

});

function getMamaFuturn() {
  var url = GLConfig.get_mama_fortune;
  $.ajax({
    "url": url,
    "type": 'get',
    "success": futurnCallBack,
    "csrfmiddlewaretoken": csrftoken
  });

  function futurnCallBack(res) {
    console.log(res.mama_fortune);
    var level = res.mama_fortune.mama_level;
    if (level == 1) {
      $(".invitation-class-gold").addClass('active');
    }
    if (level == 2) {
      $(".invitation-class-diamond").addClass('active');
    }
    if (level == 3) {
      $(".invitation-class-crown").addClass('active');
    }
    if (level == 4) {
      $(".invitation-class-gold-crown").addClass('active');
    }
  }
}

function getMamaInvitationRes() {
  var url = nextReferalPage;
  if (!url) {
    //drawToast('~');
    return;
  }
  var body = $(".invited-friends-list");

  if (body.hasClass('loading')) { // 如果没有返回则　return
    return;
  }

  body.addClass('loading');
  $.ajax({
    "url": url,
    "type": 'get',
    "success": callback,
    "csrfmiddlewaretoken": csrftoken
  });

  function callback(res) {
    console.log('res:', res);
    body.removeClass('loading');
    nextReferalPage = res.next;
    var num1 = parseInt(res.count / 100);
    var num2 = parseInt(res.count / 10) % 10;
    var num3 = res.count % 10;
    $("#invitation-num-1").html(num1); //百位数
    $("#invitation-num-2").html(num2); //十位数
    $("#invitation-num-3").html(num3); //个位数
    var users = $.each(res.results, function(i, invitation) {
      if (invitation.referal_to_mama_img === '') {
        invitation.referal_to_mama_img = 'http://7xogkj.com2.z0.glb.qiniucdn.com/1181123466.jpg';
      }
      return invitation;
    });

    if (users.length > 0) {
      $('.js-invite').after(template('invitation-res-template', { users: users }));
    }
  }
}

function loadData(func) { //动态加载数据
  var totalheight = parseFloat($(window).height()) + parseFloat($(window).scrollTop()); //浏览器的高度加上滚动条的高度
  var scroll_height = $(document).height() - totalheight;
  if ($(document).height() - 600 <= totalheight && scroll_height < 600) //当文档的高度小于或者等于总的高度的时候，开始动态加载数据
  {
    func();
  }
}
