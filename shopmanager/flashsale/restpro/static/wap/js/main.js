/**
 *@author: imeron
 *@date: 2015-07-22 
 */
function Set_posters(suffix){
	//获取海报
	var posterUrl = GLConfig.baseApiUrl + '/posters/'+ suffix +'.json';
	
	var posterCallBack = function(data){
		if (data.wem_posters != 'undifine' && data.wem_posters != null){
			//设置女装海报链接及图片
			$.each(data.wem_posters,
				function(index,poster){
					$('.poster .nvzhuang').attr('href',poster.item_link);
					$('.poster .nvzhuang img').attr('src',poster.pic_link);
					if (poster.subject === 'undifine' || poster.subject === null ){
						return
					}
					$('.poster .nvzhuang .subject').html('<span class="tips">'+poster.subject[0]+'</span>'+poster.subject[1]);
				}
			);
		}
		if (data.chd_posters != 'undifine' && data.chd_posters != null){
			//设置童装海报链接及图片
			$.each(data.chd_posters,
				function(index,poster){
					$('.poster .chaotong').attr('href',poster.item_link);
					$('.poster .chaotong img').attr('src',poster.pic_link);
					if (poster.subject === 'undifine' || poster.subject === null ){
						return
					}
					$('.poster .chaotong .subject').html('<span class="tips">'+poster.subject[0]+'</span>'+poster.subject[1]);
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
	p_obj.saleout_dom = '';
	if (p_obj.saleout){
		p_obj.saleout_dom = '<div class="mask"></div><div class="text">抢光了</div>';
	}
	//创建商品DOM
	function Item_dom(){
	/* 
	<li>
      <a href="pages/shangpinxq.html?id={{ id }}">
        <img src="{{ pic_path }}">
        <p class="gname">{{ name }}</p>
        <p class="gprice">
          <span class="nprice"><em>¥</em> {{ agent_price }} </span>
          <s class="oprice"><em>¥</em> {{ std_sale_price }}</s>
        </p>{{ saleout_dom }}
      </a>
    </li>	 */
	};
    return hereDoc(Item_dom).template(p_obj);
}

function Set_promotes_product(suffix){
	//获取今日推荐商品
	var promoteUrl = GLConfig.baseApiUrl + '/products/promote_'+ suffix +'.json';
	
	var promoteCallBack = function(data){

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

function Set_category_product(suffix){
	//获取潮流童装商品
	var promoteUrl = GLConfig.baseApiUrl + suffix;
	
	var promoteCallBack = function(data){
		if (data.results != 'undifine' && data.results != null){
			//设置女装推荐链接及图片
			$.each(data.results,
				function(index,p_obj){
					var item_dom = Create_item_dom(p_obj);
					$('.glist').append(item_dom);
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


