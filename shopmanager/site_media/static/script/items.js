//显示关联商品信息弹出框
var show_items_layer = function(ev){
	ev  =  ev  ||  window.event;
	var  target    =  ev.target  ||  ev.srcElement;
	var screenX = ev.screenX
	var screenY = ev.screenY/1.5

	var  outer_id  =  target.getAttribute('outer_id');
	var url = '/items/product/item/'+outer_id+'/?format=json'

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

	var  outer_id  =  target.getAttribute('outer_id');
	var url = '/items/product/item/'+outer_id+'/?format=json&sync_stock=yes'

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
	            layer.msg('您选择了确认。',2,1);
			    ev  =  ev  ||  window.event;
		  		var  target    =  ev.target  ||  ev.srcElement;
		  		var  outer_id  =  target.getAttribute('outer_id');
		  		var url = '/items/product/item/'+outer_id+'/?format=json'
				
		  		$.post(url, {},function(data) {
				    if (date.updates_num == 1){
				 		layer.msg('产品删除成功。',2,1);  	
				    }else{
				    	layer.msg('产品删除失败。',2,1); 
				    }
				});
			},
	    }
	});
  		
 }
 	