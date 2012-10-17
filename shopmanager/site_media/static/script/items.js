//显示关联商品信息弹出框
var show_items_layer = function(ev){
	ev  =  ev  ||  window.event;
	var  target    =  ev.target || ev.srcElement;
	var screenX = ev.screenX
	var screenY = ev.screenY/1.5
	var  outer_id  = target.parentNode.getAttribute('outer_id');
	var url = '/items/product/item/'+outer_id+'/?format=json'

	$.get(url,function(data){
		var item_num    = data.itemobjs.length
		if (data.itemobjs != 'undefine'){
			$('#item_info').html(data.layer_table);
  			$.layer({
			    shade : ['',false],
			    type : 1,
			    title : ['关联商品信息' , true],
			    area : ['1000px',(170+(item_num-1)*80).toString()+'px'],
			    offset : [screenY.toString()+'px',screenX.toString()+'px'],
			    maxWidth : 1200,
			    border : [5 , 0.3 , '#628C1C', true],
			    page : {dom : '#item_layer_table'},
			    close : function(index){
			        LAYER.close(index);
				 }
			});
		}else{
			layer.msg('获取商品关联信息失败。',2,1);
		}
	});
}
//更新库存弹出框 
var sync_stock_layer = function(ev){
	
	ev  =  ev  ||  window.event;
	var  target    =  ev.target  ||  ev.srcElement;
	var screenX = ev.screenX
	var screenY = ev.screenY/1.5

	var  outer_id  =  target.parentNode.getAttribute('outer_id');
	var url = '/items/product/item/'+outer_id+'/?format=json&sync_stock=yes'
	
	$.layer({
	    shade : ['',false],
	    area : ['auto','auto'],
	    dialog : {
	        msg:'确认同步该产品淘宝库存？',
	        btns : 2, 
	        type : 4,
	        btn : ['确认','取消'],
	        yes : function(){
	        	layer.msg('正在同步淘宝库存...',2,1);
				$.get(url,function(data){
					var item_num    = data.itemobjs.length
					if (data.itemobjs != 'undefine'){
						$('#item_info').html(data.layer_table);
			  			$.layer({
						    shade : ['',false],
						    type : 1,
						    title : ['关联商品信息' , true],
						    area : ['1000px',(item_num*150).toString()+'px'],
						    offset : [screenY.toString()+'px',screenX.toString()+'px'],
						    maxWidth : 1200,
						    border : [5 , 0.3 , '#628C1C', true],
						    page : {dom : '#layer_table'},
						    close : function(index){
						        LAYER.close(index);
							 }
						});
					}else{
						layer.msg('更新库存失败。',2,1);
					}	
				});
			},
	    }
	});
	
 }
 //删除商品弹出框	
 var remove_prod_layer = function(ev){
 	$.layer({
	    shade : ['',false],
	    area : ['auto','auto'],
	    dialog : {
	        msg:'确认删除该产品信息？',
	        btns : 2, 
	        type : 4,
	        btn : ['确认','取消'],
	        yes : function(){
	            layer.msg('正在删除...',1,1);
			    ev  =  ev  ||  window.event;
		  		var  target    =  ev.target  ||  ev.srcElement;
		  		var  outer_id  =  target.parentNode.getAttribute('outer_id');
		  		var  outer_sku_id  =  target.parentNode.getAttribute('outer_sku_id');
		  		var url = '/items/product/item/'+outer_id+'/?format=json';
		  		var params = {}
		  		if (outer_sku_id != null){
		  			params["outer_sku_id"]=outer_sku_id;
		  		} 
		  		console.log(params);
		  		$.post(url, params,function(data) {
				    if (data.updates_num > 0){
				 		window.location.reload(); 	
				    }else{
				    	layer.msg('产品删除失败。',2,1); 
				    }
				});
			},
	    }
	});		
 }
 //取消库位警告
 var cancle_stockwarn_layer = function(ev){
 	$.layer({
	    shade : ['',false],
	    area : ['auto','auto'],
	    dialog : {
	        msg:'确认已手动分配淘宝商家后台店铺库存？',
	        btns : 2, 
	        type : 4,
	        btn : ['确认','取消'],
	        yes : function(){
	            layer.msg('正在取消警告...',1,1);
			    ev  =  ev  ||  window.event;
		  		var  target    =  ev.target  ||  ev.srcElement;
		  		var  outer_id  =  target.parentNode.getAttribute('outer_id');
		  		var  outer_sku_id  =  target.parentNode.getAttribute('outer_sku_id');
		  		var url = '/items/product/modify/'+outer_id+'/?format=json';
		  		if (outer_sku_id != null){
		  			url += '&outer_sku_id='+outer_sku_id ;
		  		} 
		  		$.get(url,function(data) {
				    if (data.updates_num > 0){
				   		target.parentNode.style.display = 'none';
				    }else{
				    	layer.msg('库位警告取消失败。',2,1); 
				    }
				});
			},
	    }
	});		
 }
 //查看关联采购商品
 var show_purchase_layer = function(ev){
 	ev  =  ev  ||  window.event;
	var  target    =  ev.target || ev.srcElement;
	var screenX = ev.screenX
	var screenY = ev.screenY/1.5
	
	var  purchase_id  = target.parentNode.getAttribute('purchase_id');
	var url = '/purchases/'+purchase_id+'/?format=json'
	$.get(url,function(data){
		if (data.purchase_item != 'undefine'){
			var item_num    = data.purchase_item.purchase_productskus.length
			$('#purchase_info').html(data.layer_table);
  			$.layer({
			    shade : ['',false],
			    type : 1,
			    title : ['关联采购产品信息' , true],
			    area : ['1000px',(100+(item_num-1)*20).toString()+'px'],
			    offset : [screenY.toString()+'px',screenX.toString()+'px'],
			    maxWidth : 1200,
			    border : [5 , 0.3 , '#628C1C', true],
			    page : {dom : '#purchase_layer_table'},
			    close : function(index){
			        LAYER.close(index);
				 }
			});
		}else{
			layer.msg('获取商品关联采购产品信息失败。',2,1);
		}
	});		
 }	
 
 //产品属性信息
var product_sku_modify_layer = function(ev){
	ev  =  ev  ||  window.event;
	var  target    =  ev.target || ev.srcElement;
	var  sku_id  = target.parentNode.getAttribute('prod_sku_id');
	var url = '/items/product/sku/'+sku_id+'/?format=json'

	$.get(url,function(data){
		$('#product_sku_modify').html(data.layer_table);
		$.layer({
		    shade : ['',false],
		    type : 1,
		    title : ['修改产品属性信息' , true],
		    area : ['auto','auto'],
		    offset : ['10%','50%'],
		    maxWidth : 1500,
		    border : [5 , 0.3 , '#628C1C', true],
		    page : {dom : '#product_sku_layer'},
		    close : function(index){
		        LAYER.close(index);
			 }
		});
	});
}