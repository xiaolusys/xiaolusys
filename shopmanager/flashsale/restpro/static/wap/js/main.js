var GLConfig = {
	baseApiUrl:'/rest/v1/',
};

$(function(){
	//获取今日海报
	
	var posterUrl = GLConfig.baseApiUrl + 'posters/today.json';
	
	var posterCallBack = function(data){
		console.log('debug: poster xhr,',data.wem_posters);
		//设置女装海报链接及图片
		$.each(data.wem_posters,
			function(index,poster){
			console.log('debug: poster each,',poster,index);
				$('.poster .nvzhuang').attr('href',poster.item_link);
				$('.poster .nvzhuang img').attr('src',poster.pic_link);
			}
		);
		
		//设置童装海报链接及图片
		$.each(data.chd_posters,
			function(index,poster){
				$('.poster .chaotong').attr('href',poster.item_link);
				$('.poster .chaotong img').attr('src',poster.pic_link);
			}
		);
		
	};
	
	$.ajax({ 
		type:'get', 
		url:posterUrl, 
		data:{},//可以直接加一个函数名。 
		dataType:'json', 
		success:posterCallBack 
	}); 
})