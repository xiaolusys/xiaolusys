 //var obj = window.dialogArguments
          //alert("您传递的参数为：" + obj.name)   //可以传递参数

//增加订单重审按钮

//$(document).ready(function(){
//var trade_status = document.getElementById('id_trade_status').value;
//var trade_status='WAIT_AUDIT';
//alert("您传递的参数为：" )



//})

 function show(){

        //alert("33");
	document.getElementById("addrContent").style.display="block";
                //document.getElementById("anotherDiv").style.display="none";
       return false
	}    
 function show2(){

        //alert("44");
	document.getElementById("orderContent").style.display="block";
                //document.getElementById("anotherDiv").style.display="none";
       return false
	}    

//修改地址


 function    changeAddress(){
	var trade_id      = $('#id_check_trade').val();
	var receiver_name   = document.getElementById('id_receiver_name').value;
	var receiver_mobile = document.getElementById('id_receiver_mobile').value;
	var receiver_phone  = document.getElementById('id_receiver_phone').value;
	var receiver_state  = document.getElementById('id_receiver_state').value;
	var receiver_city   = document.getElementById('id_receiver_city').value;
	var receiver_district = document.getElementById('id_receiver_district').value;
	var receiver_address  = document.getElementById('id_receiver_address').value;
	var receiver_zip    = document.getElementById('id_receiver_zip').value;
	
	
	$.post('/trades/address/',{'trade_id':trade_id,'receiver_name':receiver_name,'receiver_mobile':receiver_mobile,
			'receiver_phone':receiver_phone,'receiver_state':receiver_state,'receiver_city':receiver_city,
			'receiver_district':receiver_district,'receiver_address':receiver_address,'receiver_zip':receiver_zip,'format':'json'},function(res){
                  // alert(res.code);

        try {
        	
               if (res.code == 0){
            	 alert("地址修改成功！");
                }else{
                  alert("地址修改失败:"+res.response_error);
                }
           } catch (err) {
                  // console.log('Error: (ajax callback) - ', err);
              } 
		},
		  'json');	
		};




//修改订单信息
function changeOrder(info){

	var target  = info;
	var idx     = target.getAttribute('idx');
	var order_id     = target.getAttribute('oid');
         
	var outer_sku_id = document.getElementById('id-select-ordersku-'+idx).value;
	var order_num    = document.getElementById('id-change-order-num-'+idx).value;
	//alert(order_id+"外部编码"+outer_sku_id+"数目"+order_num);

$.post('/trades/order/update/'+order_id+'/',{'outer_sku_id':outer_sku_id,'order_num':order_num},function(res){
                  // alert(res.code);

        try {
        	
               if (res.code == 0){
            	 var order = res.response_content;
            	var cell  = target.parentElement.parentElement;
            	cell.cells[0].innerHTML = order.id;
            	cell.cells[1].innerHTML = order.outer_id;
            	cell.cells[2].innerHTML = order.title;
            	cell.cells[3].innerHTML = order.sku_properties_name;
            	cell.cells[4].innerHTML = '<input class="order_num" type="text" value="'+order.num+'" size="8" disabled="disabled" />';
            	cell.cells[5].innerHTML = order.price;
updateTotalNum()
            	if (order.out_stock){
            		cell.cells[6].innerHTML = '<img src="/static/admin/img/icon-yes.gif" alt="True">';
            	}else{
            		cell.cells[6].innerHTML = '<img src="/static/admin/img/icon-no.gif" alt="False">';	
            	} 
				cell.cells[7].innerHTML = GIT_TYPE[order.gift_type];
				cell.cells[8].innerHTML = '';
                }else{
                  alert("订单修改失败:"+res.response_error);
                }
           } catch (err) {
                  // console.log('Error: (ajax callback) - ', err);
              } 
		},
		  'json');	
		

}



//计算数量
 function   updateTotalNum(){
//alert("计算数量");
	var total_num = 0;
	$.each($('.order_num'),function(n,obj){
		var value = obj.value;
		if(value!=''&&value!='undifine'){
			total_num += parseInt(value);
		}
	});
	$('#total_num').val(total_num+'');
}




//删除订单信息

function   deleteOrder(info){
	var target = info;
	var row    = target.parentElement.parentElement;
	var rowIndex = row.rowIndex;
	var table    = row.parentElement.parentElement;
	var order_id = target.getAttribute('oid');

	if(!confirm("确定删除订单 "+order_id+" 吗？"))
	{
	    return;
	}
	
$.post('/trades/order/delete/'+order_id+'/',function(res){
                   //alert(res.code);

        try {
        	
               if (res.code == 0){
            	table.deleteRow(rowIndex);
            	//重新计算数量
            	updateTotalNum();
                }


              else{
                alert("订单删除失败:"+res.response_error);
                }
           } catch (err) {
                  // console.log('Error: (ajax callback) - ', err);
              } 
		},
		  'json');	

}

//查询商品中----的增加行
function  addSearchRow(tableID,prod){
//alert("增加行数"+tableID);
//alert("商品"+prod);
	var table = document.getElementById(tableID);
	var rowCount = table.rows.length;
    var row = table.insertRow(rowCount);
    var index = rowCount;
  
	//var id_cell = createDTText(index+'');
    var id_cell=document.createElement('td');
        id_cell.innerHTML=index+''
	//var outer_id_cell = createDTText(prod[0]);
    var outer_id_cell=document.createElement('td');
       outer_id_cell.innerHTML=prod[0]

	//var title_cell    = createDTText(prod[1]);
   var title_cell=document.createElement('td');
       title_cell.innerHTML=prod[1]


	var sku_cell = document.createElement('td');
	var sku_options = '<select id="id-order-sku-'+index.toString()+'" class="chosen-select" >';

	for(var i=0;i<prod[3].length;i++){
		var sku = prod[3][i];
		sku_options += '<option value="'+sku[0]+'">'+sku[1]+'&raquo;'+sku[2]+'</option>';
	}
	sku_options += '</select>';
	sku_cell.innerHTML = sku_options;
	 
	var num_cell = document.createElement('td');
	num_cell.innerHTML = '<input id="id-order-num-'+index.toString()+'" type="text" class="prod_num" value="1" size="2" />';
	 
	//var price_cell = createDTText(prod[2]);
	var price_cell=document.createElement('td');
        price_cell.innerHTML=prod[2]



	var addbtn_cell = document.createElement('td');
	var trade_type  = document.getElementById('id_trade_type').value;

	if (trade_type=='EXCHANGE_TRADE_TYPE'){
		addbtn_cell.innerHTML = '<button  id="add-order"  onclick="addOrder(this)"  class="add-order btn-mini" outer_id="'+prod[0]+'" idx="'+index.toString()+'" action="return"'+'">退货</button>'
								+'<button class="add-order btn-mini" outer_id="'+prod[0]+'" idx="'+index.toString()+'" action="change"'+'">换货</button>';
	}else{
		addbtn_cell.innerHTML = '<button  id="add-order" onclick="addOrder(this)"    class="add-order btn-success" outer_id="'+prod[0]+'" idx="'+index.toString()+'" action="present"'+'">添加</button>';
	}
	//alert("到这里"+index);//到了
	row.appendChild(id_cell);
	row.appendChild(outer_id_cell);
	row.appendChild(title_cell);
	row.appendChild(sku_cell);
	row.appendChild(num_cell);
	row.appendChild(price_cell);
	row.appendChild(addbtn_cell);	
}










//查询商品
function  searchProd(info){
//alert("搜索");


	var sch_table = document.getElementById('id-search-table');
	
	//goog.style.showElement(sch_table,true);
	var q = document.getElementById('id-search-q').value;
	if (!q){
		return;
	}
      
	var that = this;
	for(var i=sch_table.rows.length;i>1;i--){
		sch_table.deleteRow(i-1);
	}
	var params = {'q':q};
$.get('/trades/orderplus/', {'q':q},function(res){
                   //alert("编码"+res.response_content[0]);
                console.info(res.response_content[0]);
            
        try {
            //alert("开锁555"+res.code);
        	//var res = res1.getResponseJson();
                // alert(res.code);
               if (res.code == 0){
                 document.getElementById("id-search-table").style.display="block";
            	for(var i=0;i<res.response_content.length;i++){
                      //  alert("开始进入55");
            		addSearchRow('id-search-table',res.response_content[i]);
            	}
            	var addOrderBtns = $('#add-order');
              //alert("开始进入55");
            // console.info(addOrderBtns[0]);
            	//for(var i=0;i<addOrderBtns.length;i++){
            		//goog.events.listen(addOrderBtns[i], goog.events.EventType.CLICK,that.addOrder,false,that);
            	//}

                }


              else{
                alert("商品查询失败:"+res.response_error);
                }
           } catch (err) {
                   console.log('Error: (ajax callback) - ', err);
              } 
		},
		  'json');
}

//增加订单行
 function addOrderRow(tableID,order){
       // alert("add订单开始");
console.info(order);
	var table = document.getElementById(tableID);
	var tbody = table.tBodies;
	if (!tbody){
		return;
	}
	var row =document.createElement('tr');
    
	//var id_order_cell = createDTText(order.id+'');
         var id_order_cell=document.createElement('td');
        id_order_cell.innerHTML=order.id+''
        
	//var outer_id_cell = createDTText(order.outer_id);
        var outer_id_cell=document.createElement('td');
        outer_id_cell.innerHTML=order.outer_id

	//var title_cell    = createDTText(order.title);
        var title_cell=document.createElement('td');
        title_cell.innerHTML=order.title

	//var sku_properties_name_cell = createDTText(order.sku_properties_name);
        var sku_properties_name_cell=document.createElement('td');
       sku_properties_name_cell.innerHTML=order.sku_properties_name
        


	var num_cell = document.createElement('td');
	num_cell.innerHTML = '<input class="order_num" type="text" value="'+order.num+'" size="8" />';
	
	//var price_cell = createDTText(order.price);
        var price_cell=document.createElement('td');
       price_cell.innerHTML=order.price

       
    

	var stock_status_cell   = document.createElement('td');
	if (order.out_stock){
		stock_status_cell.innerHTML = '<img src="/static/admin/img/icon-yes.gif" alt="True">';
	}else{
		stock_status_cell.innerHTML = '<img src="/static/admin/img/icon-no.gif" alt="False">';	
	}
	//var gift_type_name = GIT_TYPE[order.gift_type];
	//alert(gift_type_name);
	//var gift_type_cell  = createDTText(gift_type_name);
        var gift_type_name="";
 if (order.gift_type == 0 ){ gift_type_name="实付"  }
 else if (order.gift_type ==1 ){  gift_type_name=  "赠送"   }
else if (order.gift_type == 2){  gift_type_name=  "满就送"   }
else if (order.gift_type == 3){  gift_type_name=  "拆分"   }
else if (order.gift_type == 4){  gift_type_name= "退货"    }
else if (order.gift_type == 5){  gift_type_name= "换货"    }
else {  gift_type_name=  "其他"   }


        var gift_type_cell=document.createElement('td');
       gift_type_cell.innerHTML= gift_type_name;
        

	var delete_btn_cell = document.createElement('td');
	delete_btn_cell.innerHTML = '<button class="delete-order btn-danger"  onclick="deleteOrder(this)" oid="'+order.id.toString()+'">删除</button>';
	
	row.appendChild(id_order_cell);
	row.appendChild(outer_id_cell);
	row.appendChild(title_cell);
	row.appendChild(sku_properties_name_cell);
	row.appendChild(num_cell);
	row.appendChild(price_cell);
	row.appendChild(stock_status_cell);
	row.appendChild(gift_type_cell);
	row.appendChild(delete_btn_cell);
	
	tbody[0].appendChild(row);
       
}

























//////
//添加订单
function addOrder(info){
 // alert("进入");
    var that = this;
	var target = info;
	var idx    = target.getAttribute('idx');
	var action = target.getAttribute('action');
	var trade_id     = document.getElementById('id_check_trade').value;
	var outer_id     = target.getAttribute('outer_id');
	var sku_outer_id = document.getElementById('id-order-sku-'+idx).value;
	var num          = document.getElementById('id-order-num-'+idx).value;
	var order_type   = null;
	//alert("进入idx"+action);
	if (action=="return"){
		order_type = "RETURN_GOODS_TYPE";
	}else if (action=="change"){
		order_type = "CHANGE_GOODS_TYPE";
	}else{
		order_type = "HANDSEL_TYPE";
	}
	
	var params     = {'trade_id':trade_id,'outer_id':outer_id,'outer_sku_id':sku_outer_id,'num':num,'type':order_type}
        //alert("函数开始");
        
$.post('/trades/orderplus/', {'trade_id':trade_id,'outer_id':outer_id,'outer_sku_id':sku_outer_id,'num':num,'type':order_type},function(res){
                  // alert("编码");
               // console.info(res.response_content);
            
        try {
               if (res.code == 0){
                 //alert("增加行数");
            	addOrderRow('id_trade_order',res.response_content);
		// alert("成功");		
				updateTotalNum();


                }
              else{
                alert("添加失败:"+res.response_error);
                }
           } catch (err) {
                   //console.log('Error: (ajax callback) - ', err);
              } 
		},
		  'json');

}



function ordercheck(info){
var action_code = '';
    if (info.getAttribute('key') == 'CHECK') {
        action_code = 'check';
   
    }else if (info.getAttribute('key') == 'REVIEW'){
        action_code = 'review';
      // alert("review");
    }
   var tradeDom  = document.getElementById("id_check_trade").value;
    var logisticsDom = document.getElementById("id_logistics").value;
    var priorityDom  = document.getElementById("id_priority").value;
    var shippingDom  = document.getElementById("id_shipping_type").value;
    //
    var trade_id  = $('#id_check_trade').val();

$.post('/trades/checkorder/'+trade_id+'/?format=json', {
					'format':'json',
					'logistic_code': logisticsDom,
					'priority':priorityDom,
					'shipping_type':shippingDom,
					'action':action_code
},function(res){
              var that  = this;
           try {
               if (res.code == 0){
                alert("审核成功");
               window.close();
                }
              else{
                alert("审核失败:"+res.response_error);
                }
           } catch (err) {
                   console.log('Error: (ajax callback) - ', err);
              } 
		},
		  'json');

}


