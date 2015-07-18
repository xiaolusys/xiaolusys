
function Set_posters(suffix){
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

function Create_item_dom(p_obj){
	var ht = '<li>'
      + '<a href="pages/details.html?item_id='+ p_obj.id +'">'
      + '<img src="'+ p_obj.pic_path +'">'
      + '<p class="gname">'+ p_obj.name +'</p>'
      + '<p class="gprice">'
      + '<span class="nprice"><em>¥</em>'+ p_obj.agent_price +'</span>'
      + '<s class="oprice"><em>¥</em> '+ p_obj.std_sale_price +'</s>'
      + '</p></a></li>';
    return ht;
}

function Set_promotes_product(suffix){
	//获取今日推荐商品
	var promoteUrl = GLConfig.baseApiUrl + 'products/promote_'+ suffix +'.json';
	
	var promoteCallBack = function(data){
		console.log('debug type:',typeof(data.female_list));
		if (data.female_list != 'undifine' && data.female_list != null){
			
			$('.glist .nvzhuang').empty();
			//设置女装推荐链接及图片
			$.each(data.female_list,
				function(index,p_obj){
					var item_dom = Create_item_dom(p_obj);
					$('.glist .nvzhuang').append(item_dom);
				}
			);
		}
		
		if (data.child_list != 'undifine' && data.child_list != null){
			
			$('.glist .chaotong').empty();
			//设置童装推荐链接及图片
			$.each(data.child_list,
				function(index,p_obj){
					var item_dom = Create_item_dom(p_obj);
					$('.glist .chaotong').append(item_dom);
				}
			);
		}
	};
	// 请求推荐数据
	$.ajax({ 
		type:'get', 
		url:promoteUrl, 
		data:{}, 
		dataType:'json', 
		success:promoteCallBack 
	}); 
	
}

