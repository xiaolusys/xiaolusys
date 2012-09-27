
var show_layer = function(ev){
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
			}
  		});
  	}