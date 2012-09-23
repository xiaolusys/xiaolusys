/**************************************************************

 @Name : jQuery-plugin-layer v1.4 开发版
 @author: 贤心
 @date: 2012-9-15
 @blog: http://xu.sentsin.com/
 @微博：http://t.qq.com/xian_xin
 @QQ群：176047036(前端超级群,js面向对象) 176047238(舞动JavaScript)
 @Copyright: Sentsin Xu(贤心)
 @官网说明：http://xu.sentsin.com/jquery/layer/
 @desc: 1、为便于版本管理，layer将不在用0作为起始版本，开始采用1起始（v1.4）
 		2、为加强性能，v1.4开始采用全新的参数规则，将不再对之前所有版本(v0.1
		-v0.3)的参数兼容。请务必尽快放弃老版本，对此造成的不便贤心深感歉意。
		
 *************************************************************/ 

void function(L , DOM){		
	var ready = {
		getPath : function(){
			var js = document.scripts || L("script");
			var jsPath = js[js.length - 1].src;
			return jsPath.replace(jsPath.split('/')[jsPath.split('/').length-1],'');
		},
		append : function(){
			var ie6PNG = '<!--[if IE 6]><script type="text/javascript" src="'+ this.getPath() +'skin/png.js"></script><![endif]-->';
			document.write('\n' + '<link rel="stylesheet" type="text/css" href="'+ this.getPath() +'skin/layer.css"  />' + '\n' + ie6PNG);
			this.global();
		},
		global : function(){
			iE6 = !-[1,] && !window.XMLHttpRequest;
			times = 0; //追寻索引
		}
	};
	ready.append();
	function FUNC(){};
	FUNC.prototype = { //layer默认内置方法，其它形式都可通过$.layer()任意拓展。
		v : '1.4',	//The current version of layer being used
		alert : function(alertMsg , alertType, alertTit , alertYes){	//普通对话框，类似系统默认的alert()
			return $.layer({
				dialog : {
					msg : alertMsg,
					type : alertType,
					yes : alertYes
				},
				title : alertTit
			});
		},
		confirm : function(conMsg  , conYes , conTit , conNo){ //询问框，类似系统默认的confirm()
			return $.layer({
				dialog : {
					msg : conMsg,
					type : 4,
					btns : 2,
					yes : conYes,
					no : conNo
				},
				title : conTit
			}); 
		},
		msg : function(msgText , msgTime , msgType , maxWidth){ //普通消息框，一般用于行为成功后的提醒,默认两秒自动关闭
			(msgText == '' || msgText == undefined) && (msgText = '&nbsp;');
			(msgTime == undefined || msgTime == '') && (msgTime = 2);
			return $.layer({
				dialog : {
					msg : msgText,
					type : msgType,
					maxWidth : maxWidth
				},
				time : msgTime,
				title : ['',false],
				closeBtn : ['',false]
			});	
		},
		tips : function(html , follow , time , maxWidth){
			return $.layer({
				type : 4,
				shade : false,
				time : time,
				maxWidth : maxWidth,
				tips : {msg : html , follow : follow}	
			})
		},
		load : function(loadTime , loadgif , loadShade){
			var border = true;
			loadgif == 3 && (border = false);
			return $.layer({
				time : loadTime,
				shade : loadShade,
				loading : {type : loadgif},
				border :[10,0.3,'#000',border],
				type : 3,
				title : ['',false],
				closeBtn : [0 , false]
			}); 
		}
	};
	layer = new FUNC();
	function CLASS(options){
		this.init(options)
	};
	CLASS.prototype = {
		type : function(){
			var arry = ['dialog' , 'page' , 'iframe' , 'loading' , 'tips'];
			return arry;	
		},
		config : { //默认配置
			skin : 0,
			shade : [0.5 , '#000' , true],
			fix : true,
			move : ['.xubox_title' , true],
			type : 0,
			title : ['信息' , true],
			offset : ['220px' , '50%'],
			area : ['310px' , 'auto'],
			closeBtn : [0 , true],
			time : 0,
			border : [10 , 0.3 , '#000', true],
			zIndex : 19891014, 
			maxWidth : 400,
			fadeIn : [300 , false],
			dialog : {
				btns : 1,
				btn : ['确定','取消'],
				type : 3,
				msg : '',
				yes : function(index){ LAYER.close(index);}, //按钮一回调
				no : function(index){ LAYER.close(index);} //按钮二回调
			},
			page : {dom : '#xulayer'},
			iframe : {src : 'http://xu.sentsin.com'},
			loading : {type : 0},
			tips : {
				msg : '',
				follow : ''
			},
			success : function(layer){}, //layer创建成功后的回调
			close : function(index){ LAYER.close(index);}, //右上角关闭回调
			end : function(){} 
		},
		init : function(setings){
			times++;
			config = $.extend({} , this.config  , setings);
			dialog = $.extend({}, this.config.dialog , setings.dialog);
			page = $.extend({}, this.config.page , setings.page);
			iframe = $.extend({}, this.config.iframe , setings.iframe);	
			loading = $.extend({}, this.config.loading , setings.loading);
			tips = $.extend({}, this.config.tips , setings.tips);			
			this.adjust();
		},
		space : function(){ //层容器
			var frame = [
				'<div class="xubox_dialog"><span class="xubox_msg xulayer_png32 xubox_msgico xubox_msgtype' + dialog.type + '"></span><span class="xubox_msg xubox_text">' + dialog.msg + '</span></div>',	
				'<div class="xubox_page xubox_page_' + config.skin + '"></div>',
				'<iframe id="xubox_iframe" name="xubox_iframe" class="xubox_iframe" frameborder="0" src="' + iframe.src + '"></iframe>',				
				'<span class="xubox_loading xubox_loading_'+ loading.type +'"></span>',
				'<div class="xubox_tips xubox_tips_' + config.skin +'"><div class="xubox_tipsMsg">'+ tips.msg +'</div><i class="xulayer_png32"></i></div>'
			];			
			var shade = '' , border = '';
			zIndex = config.zIndex + times;
			var shadeStyle = "z-index:"+ zIndex +"; background:"+ config.shade[1] +"; opacity:"+ config.shade[0] +"; filter:'alpha(opacity="+ config.shade[0]*100 +")'; filter:alpha(opacity="+ config.shade[0]*100 +");";
			config.shade[2] && (shade = '<div id="xubox_shade' + times + '" class="xubox_shade xubox_shade_' + config.skin + '" style="'+ shadeStyle +'"></div>');	
			var borderStyle = "z-index:"+ (zIndex-1) +";  background: "+ config.border[2] +"; opacity:"+ config.border[1] +"; filter:'alpha(opacity="+ config.border[1]*100 +")'; filter:alpha(opacity="+ config.border[1]*100 +"); top:-"+ config.border[0] +"px; left:-"+  config.border[0] +"px;";
			config.border[3] && (border = '<div id="xubox_border'+ times +'" class="xubox_border" style="'+ borderStyle +'"></div>');
			var boxhtml = '<div times="'+ times +'" showtime="'+ config.time +'" style="z-index:'+ zIndex +'" id="xubox_layer'+ times +'" class="xubox_layer xubox_layer_' + config.skin + '">'	
				+ '<div style="z-index:'+ zIndex +'" class="xubox_main xubox_main_' + config.skin + '">'
				+ frame[config.type]
				+ '<h2 class="xubox_title xubox_title_' + config.skin + '"><i class="xulayer_png32"></i><em>' + config.title[0] + '</em></h2>'
				+ '<a class="xubox_close xulayer_png32 xubox_close' + config.closeBtn[0] + '_' + config.skin + '" href="javascript:;"></a>'
				+ '<span class="xubox_botton"></span>'
				+ '</div>'+ '<textarea class="xubox_inputClose" type="hidden" style="display:none">'+ String(config.close) +'</textarea>' + border + '</div>';
			return [shade , boxhtml];
		},
		adjust : function(){ //插入layer
			var othis = this , space = '';
			var setSpace = function(){
				space = othis.space();
				$("body").append(space[0]);
			};
			switch(config.type){
				case 1:
					setSpace();
					if($(page.dom).parents('.xubox_page').length == 0){
						$(page.dom).show().wrap(space[1]);
					}else{
						return false;	
					}
				break;
				case 2:
					setSpace();
					$('.xubox_layer').find('.xubox_iframe').length > 0 && $('.xubox_iframe').parents('.xubox_layer').remove();
					$("body").append(space[1]);
				break;
				case 3:
					 config.title = ['',false];
					 config.area = ['auto','auto']; 
					 config.closeBtn = ['',false];
					 setSpace();
					 $('.xubox_layer').find('.xubox_loading').length > 0 &&  $('.xubox_loading').parents('.xubox_layer').remove();
					 $("body").append(space[1]);
				break;
				case 4:
					config.title = ['',false];
					config.area = ['auto','auto'];
					config.fix = false;
					config.border = [0,0,0,false];
					setSpace();
					$('.xubox_layer').find('.xubox_tips').length > 0 && $('.xubox_tips').parents('.xubox_layer').remove();
					$("body").append(space[1]);
					$('.xubox_tips').fadeIn(200).parents('.xubox_layer').find('.xubox_close').css({top : 5 , right : 5})
				break;
				default : 
					config.title[1] || (config.area = ['auto','auto']);
					setSpace();
					$('.xubox_layer').find('.xubox_dialog').length > 0 && $('.xubox_dialog').parents('.xubox_layer').remove();
					$("body").append(space[1]);
				break;
			};
			
			layerS = $('#xubox_shade' + times);
			layerB = $('#xubox_border' + times);
			layerE = $('#xubox_layer' + times);		
			//设置layer面积坐标等数据 
			var _mleft = layerE.outerWidth()/2;
			if(config.offset[1].indexOf("px") != -1){
				var _left = _mleft + parseInt(config.offset[1]);
			}else{
				if(config.offset[1] == '50%'){
					var _left =  config.offset[1];
				}else{
					var _left =  _mleft + parseInt(config.offset[1])/200*$(window).width();
				}
			};
			layerE.css({'left' : _left + config.border[0] , 'width' : config.area[0] , 'height' : config.area[1]});
			config.fix ? layerE.css({'top' : config.offset[0]}) : layerE.css({'top' : parseInt(config.offset[0]) + $(window).scrollTop() , 'position' : 'absolute'});	
			layerMian = layerE.find('.xubox_main');
			layerTitle = layerE.find('.xubox_title');
			layerText = layerE.find('.xubox_text');
			layerPage = layerE.find('.xubox_page');
			layerBtn = layerE.find('.xubox_botton');			
			//配置按钮 对话层形式专有
			if(config.type == 0 && config.title[1]){
				switch(dialog.btns){
					case 0:
						layerBtn.html('').hide();
						break;
					case 2:
						layerBtn.html('<a href="javascript:;" class="xubox_yes xubox_botton2_' + config.skin + '">' + dialog.btn[0] + '</a>' + '<a href="javascript:;" class="xubox_no xubox_botton3_' + config.skin + '">' + dialog.btn[1] + '</a>');
						break;
					default:
						layerBtn.html('<a href="javascript:;" class="xubox_yes xubox_botton1_' + config.skin + '">' + dialog.btn[0] + '</a><a class="xubox_no" style="displa:none;"></a>');
				}
			};
			this.pagetype();
			this.callback(config);
		},
		pagetype : function(){ //调整layer			
			var othis = this;
			othis.autoArea();
			config.time == 0 || this.autoclose();
			config.move[1] ? layerE.find('.xubox_title').css({'cursor':'move'}) : layerE.find('.xubox_title').css({'cursor':'auto'});		
			config.closeBtn[1] || layerE.find('.xubox_close').remove().hide();
			if(!config.title[1]){
				layerE.find('.xubox_title').remove().hide();
				config.type != 4 && layerE.find('.xubox_close').removeClass('xubox_close0_' + config.skin).addClass('xubox_close1_' + config.skin);
			}else{
				layerTitle.css({width : layerE.outerWidth()});	
			};		
			config.border || layerE.removeClass('xubox_layerBoder');
			var maRight = parseInt(layerMian.css('margin-right'));	
			var paBottom = parseInt(layerE.css('padding-bottom'));
			layerE.attr({'type' :  othis.type()[config.type]});
			switch(config.type){
				case 1: 	
					layerE.find(page.dom).addClass('layer_pageContent');
					layerPage.css({'width' : layerE.width() - 2*maRight});
					config.shade && layerE.css({'z-index' : zIndex + 1});
					config.title[1] ? layerPage.css({'top' : maRight + layerTitle.outerHeight()}) : layerPage.css({'top' : maRight});
				break;
				case 2:
					layerE.find('.xubox_iframe').addClass('xubox_load').css({'width' : layerE.width() - 2*maRight});
					config.title[1] ? layerE.find('.xubox_iframe').css({'top' : layerTitle.height() + paBottom ,'height' : layerE.height() - layerTitle.height()}): layerE.find('.xubox_iframe').css({top : paBottom , height : layerE.height()});
					iE6 && layerE.find('.xubox_iframe').attr("src" , iframe.src);
				break;
				case 4 :
					var top = $(tips.follow).offset().top - $(tips.follow).outerHeight() - layerE.outerHeight();
					var left = $(tips.follow).offset().left + layerE.outerWidth()/2;
					layerE.css({top : top , left : left});
				break;	
				default :
					if(config.title[1]){
						layerText.css({paddingTop : 18 + layerTitle.outerHeight()});
					}else{
						layerE.find('.xubox_msgico').css({top : '10px'});
						layerText.css({marginTop : 12})	
					}
				break;
			};
			var fadeTime = 0; config.fadeIn[1] && (fadeTime = config.fadeIn[0]);
			layerE.animate({opacity : 1 , filter : 'alpha(opacity='+ 100 +')'},fadeTime);
			this.move();
		},
		autoArea : function(){ //自适应宽高
			if(config.area[0] == 'auto' && layerMian.outerWidth() >= config.maxWidth){	
				layerE.css({width : config.maxWidth});
			}
			config.title[1] ? titHeight =  layerE.find('.xubox_title').innerHeight() : titHeight = 0;
			switch(config.type){
				case 0:
					var aBtn = layerBtn.find('a');
					var outHeight =  layerText.outerHeight() + 20;
					if(aBtn.length > 0){
						var btnHeight = layerBtn.find('a').outerHeight() +  parseInt(layerBtn.find('a').css('bottom')) + 10;
					}else{
						var btnHeight = 0;
					}
				break;
				case 1:
					var btnHeight = 0,outHeight = $(page.dom).outerHeight();
					layerE.css({width : layerPage.outerWidth()});
				break;
				case 3:
					var btnHeight = 0; var outHeight = $(".xubox_loading").outerHeight(); 
					layerMian.css({width : $(".xubox_loading").width()});
				break;
			};
			layerE.css({marginLeft : -layerE.outerWidth()/2});
			config.area[1] == 'auto' && layerMian.css({height : titHeight + outHeight + btnHeight});
			layerB.css({'width' : layerE.outerWidth() + 2*config.border[0] , 'height' : layerE.outerHeight() + 2*config.border[0]});
			(iE6 && config.area[0] != 'auto') && layerMian.css({width : layerE.outerWidth()});
		},	
		move : function(){ //拖拽层		
			var layerMove = layerE.find(config.move[0]);
			config.move[1] && layerMove.attr('move','ok');
			$(config.move[0]).mousedown(function(M){	
				var layerE = $(this).parents('.xubox_layer');
				if($(this).attr('move') == 'ok'){
					var ismove = true; 
					var moveX = M.pageX - parseInt(layerE.position().left);
					var moveY = M.pageY - parseInt(layerE.position().top);						
					$(document).mousemove(function(M){
						if(ismove){
							var x = M.pageX - moveX;
							if(layerE.css('position') == 'fixed'){
								var y = M.pageY - moveY - $(window).scrollTop();	
							}else{
								var y = M.pageY - moveY;	
							}
							layerE.css({"left" : x , "top" : y});										
						}					  						   
					}).mouseup(function(){
						ismove = false;
					});
				}
			});
		},
		getIndex : function(selector){ //获取layer当前索引
			return $(selector).parents('.xubox_layer').attr('times');
		},
		getChildFrame : function(selector){ //获取子iframe的DOM
			return $("#xubox_iframe").contents().find(selector);
		},
		getFrameIndex : function(){ //得到iframe层的索引，子iframe时使用
			return $('#xubox_iframe').parents('.xubox_layer').attr('times');
		},
		close : function(index){ //关闭layer
			var layerNow = $('#xubox_layer' + index);
			var shadeNow = $('#xubox_shade' + index);
			if(layerNow.attr('type') == this.type()[1]){
				layerNow.find('.xubox_close,.xubox_botton,.xubox_title,.xubox_border').remove();
				for(i = 0 ; i < 3 ; i++){
					layerNow.find('.layer_pageContent').unwrap().hide();
				}
			}else{
				layerNow.remove();
			}
			shadeNow.remove();
			iE6 && this.reselect();	
			config.end();
		},
		loadClose : function(){ //关闭加载层，仅loading私有
			var parent = $('.xubox_loading').parents('.xubox_layer');
			var index = parent.attr('times');
			$('#xubox_shade' + index).remove();
			parent.remove();
		},
		shift : function(type , rate){ //layer内置动画
			var othis = this;
			switch(type){
				case 'left-top':
					layerE.css({left : layerE.outerWidth()/2 + config.border[0] , top : -layerE.outerHeight()}).animate({top : config.border[0]},rate,function(){
						iE6 && othis.IE6();	
					});
				break; 
				case 'right-top':
					layerE.css({left : $(window).width() - layerE.outerWidth()/2 - config.border[0] , top : -layerE.outerHeight()}).animate({top : config.border[0]},rate,function(){
						iE6 && othis.IE6();	
					});
				break; 
				case 'left-bottom':
					layerE.css({left : layerE.outerWidth()/2 + config.border[0] , top : $(window).height()}).animate({top : $(window).height() - layerE.outerHeight() - config.border[0]},rate,function(){
						iE6 && othis.IE6();	
					});
				break; 
				case 'right-bottom':
					layerE.css({left :  $(window).width() - layerE.outerWidth()/2 - config.border[0] , top : $(window).height()}).animate({top : $(window).height() - layerE.outerHeight() - config.border[0]},rate,function(){
						iE6 && othis.IE6();	
					});
				break;
			};
		},
		autoclose : function(){ //自动关闭layer
			$.each($('.xubox_layer'),function(){
				var layerE = $(this);
				var time = $(this).attr('showtime');
				function maxLoad(){
					time--;
					time == 0 && LAYER.close(layerE.attr('times'));
					$('.xubox_layer').length < 1 && clearInterval(autotime);
				};
				autotime = setInterval(maxLoad , 1000);
			});
		},
		callback : function(deliver){
			LAYER = this;
			config.success(layerE);
			iE6 && this.IE6();
			$('.xubox_close').unbind('click').bind('click',function(){
				var index = $(this).parents('.xubox_layer').attr('times');
				var closeFn = $(this).parents('.xubox_layer').find('.xubox_inputClose').val();
				eval('(' + closeFn + ')('+ index +')');
			});
			layerE.find('.xubox_yes').live('click',function(){
				var index = $(this).parents('.xubox_layer').attr('times');
				dialog.yes(index)
			});
			layerE.find('.xubox_no').live('click',function(){
				var index = $(this).parents('.xubox_layer').attr('times');
				dialog.no(index)
			});
		},
		IE6 : function(){
			var ie6Shade =  function(){ //ie6的遮罩
				var winDOM = [$(document).width(),$(document).height(),$(window).width()];
				winDOM[0] > winDOM[1] && (winDOM[0] = winDOM - 17); //17为ie6滚动条宽度。
				layerS.css({width : winDOM[0] , height : winDOM[1]});		
			};
			ie6Shade();
			$(window).resize(ie6Shade).scroll(ie6Shade);	
			var _ieTop =  layerE.offset().top;	
			if(config.fix){ //ie6的固定与相对定位
				var ie6Fix = function(){
					layerE.css({top : $(document).scrollTop() + _ieTop});
				};	
			}else{
				var ie6Fix = function(){
					layerE.css({top : _ieTop});	
				};
			}
			ie6Fix();
			$(window).scroll(ie6Fix);
			$.each($('select'),function(index , value){ //隐藏select
				$(this).css('display') == 'none' || $(this).attr({'layer' : '1'}).hide(); 
			});
			this.reselect = function(){ //恢复select
				$.each($('select'),function(index , value){
					($(this).attr('layer') == 1 && $('.xubox_layer').length < 1) && $(this).removeAttr('layer').show(); 
				});
			};
			DD_belatedPNG.fix(".xulayer_png32"); //ie6的png32透明		
		}
	};
	$.layer = function(deliver){		
		var liver = $.extend({},deliver);
		return new CLASS(liver);
	};
}(jQuery , document);