(function(){
  var oViewport = document.getElementById('viewport');
  var phoneWidth = parseInt(window.screen.width);
  var phoneScale = phoneWidth/640;
  var ua = navigator.userAgent;

  if(/Android (\d+\.\d+)/.test(ua)){
    var version = parseFloat(RegExp.$1);
    if(version>2.3){
      oViewport.setAttribute('content','width=640, minimum-scale = '+ phoneScale +', maximum-scale = '+ phoneScale +', target-densitydpi=device-dpi')
    }else{
      oViewport.setAttribute('content','width=640, target-densitydpi=device-dpi');
    }
  } else {
    oViewport.setAttribute('content', 'width=640, user-scalable=no, target-densitydpi=device-dpi');
  }

  window.onload = function(){
    document.body.addEventListener('touchstart', function (){});
  }
})();

//全局配置
var GLConfig = {
	baseApiUrl:'/rest/v1/',
	today_suffix:'today',
    previous_suffix:'previous'
};