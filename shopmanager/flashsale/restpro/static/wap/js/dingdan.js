
function Set_orders(suffix){
	//获取海报
	var posterUrl = GLConfig.baseApiUrl + 'posters/'+ suffix +'.json';
	
	var posterCallBack = function(data){
		if (data.wem_posters != 'undifine' && data.wem_posters != null){
			//设置女装海报链接及图片
			$.each(data.wem_posters,
				function(index,poster){
				console.log('debug: poster each,',poster,index);
					$('.poster .nvzhuang').attr('href',poster.item_link);
					$('.poster .nvzhuang img').attr('src',poster.pic_link);
				}
			);
		}
		if (data.chd_posters != 'undifine' && data.chd_posters != null){
			//设置童装海报链接及图片
			$.each(data.chd_posters,
				function(index,poster){
					$('.poster .chaotong').attr('href',poster.item_link);
					$('.poster .chaotong img').attr('src',poster.pic_link);
				}
			);
		}
	};
	// 请求海报数据
	$.ajax({ 
		type:'get', 
		url:posterUrl, 
		data:{}, 
		dataType:'json', 
		success:posterCallBack 
	}); 
}