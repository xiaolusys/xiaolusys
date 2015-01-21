goog.provide('ordercheck');
goog.provide('ordercheck.Dialog');

goog.require('goog.dom');
goog.require('goog.ui.Dialog');
goog.require('goog.ui.Zippy');
goog.require('goog.style');

goog.require('goog.net.XhrIo');
goog.require('goog.uri.utils');

var updateTotalNum = function(){
	var total_num = 0;
	$.each($('.order_num'),function(n,obj){
		var value = obj.value;
		if(value!=''&&value!='undifine'){
			total_num += parseInt(value);
		}
	});
	$('#total_num').val(total_num+'');
}

var validInputNum = function(e){
	e.preventDefault();
	var target = e.target;
	var num = target.value;
	var r = /^[0-9]{1,10}$/;
	var re = new RegExp(r);
	if (!re.test(num)){
		target.value = '1';
	}
}

var addSearchRow  = function(tableID,prod){

	var table = goog.dom.getElement(tableID);
	var rowCount = table.rows.length;
    var row = table.insertRow(rowCount);
    var index = rowCount;
    
	var id_cell = createDTText(index+'');
	var outer_id_cell = createDTText(prod[0]);
	var title_cell    = createDTText(prod[1]);
	var sku_cell = goog.dom.createElement('td');
	var sku_options = '<select id="id-order-sku-'+index.toString()+'" class="chosen-select" >';
	for(var i=0;i<prod[3].length;i++){
		var sku = prod[3][i];
		sku_options += '<option value="'+sku[0]+'">'+sku[1]+'&raquo;'+sku[2]+'</option>';
	}
	sku_options += '</select>';
	sku_cell.innerHTML = sku_options;
	
	var num_cell = goog.dom.createElement('td');
	num_cell.innerHTML = '<input id="id-order-num-'+index.toString()+'" type="text" class="prod_num" value="1" size="2" />';
	
	var price_cell = createDTText(prod[2]);
	
	var addbtn_cell = goog.dom.createElement('td');
	var trade_type  = goog.dom.getElement('id_trade_type').value;
	if (trade_type==EXCHANGE_TRADE_TYPE){
		addbtn_cell.innerHTML = '<button class="add-order btn-mini" outer_id="'+prod[0]+'" idx="'+index.toString()+'" action="return"'+'">退货</button>'
								+'<button class="add-order btn-mini" outer_id="'+prod[0]+'" idx="'+index.toString()+'" action="change"'+'">换货</button>';
	}else{
		addbtn_cell.innerHTML = '<button class="add-order btn-mini" outer_id="'+prod[0]+'" idx="'+index.toString()+'" action="present"'+'">添加</button>';
	}
	
	row.appendChild(id_cell);
	row.appendChild(outer_id_cell);
	row.appendChild(title_cell);
	row.appendChild(sku_cell);
	row.appendChild(num_cell);
	row.appendChild(price_cell);
	row.appendChild(addbtn_cell);	
}

var addOrderRow  = function(tableID,order){

	var table = goog.dom.getElement(tableID);
	var tbody = table.tBodies;
	if (!tbody){
		return;
	}
	var row = goog.dom.createElement('tr');
    
	var id_order_cell = createDTText(order.id+'');
	var outer_id_cell = createDTText(order.outer_id);
	var title_cell    = createDTText(order.title);
	var sku_properties_name_cell = createDTText(order.sku_properties_name);

	var num_cell = goog.dom.createElement('td');
	num_cell.innerHTML = '<input class="order_num" type="text" value="'+order.num+'" size="8" />';
	
	var price_cell = createDTText(order.price);
	var stock_status_cell   = goog.dom.createElement('td');
	if (order.out_stock){
		stock_status_cell.innerHTML = '<img src="/static/admin/img/icon-yes.gif" alt="True">';
	}else{
		stock_status_cell.innerHTML = '<img src="/static/admin/img/icon-no.gif" alt="False">';	
	}
	var gift_type_name = GIT_TYPE[order.gift_type];
	
	var gift_type_cell  = createDTText(gift_type_name);
	var delete_btn_cell = goog.dom.createElement('td');
	delete_btn_cell.innerHTML = '<button class="delete-order btn-mini" oid="'+order.id.toString()+'">删除</button>';
	
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

/** @constructor */
ordercheck.Dialog = function (manager) {
    this.dialog = new goog.ui.Dialog();
    this.orderManager = manager;
    this.trade_id = null; 
    this.clickPos = null;
}

ordercheck.Dialog.prototype.init = function (id) {
	var dialog = this.dialog ;
    var that   = this ;
    dialog.setContent('');
    var callback = function(e){
        var xhr = e.target;
        try {
        	var res = xhr.getResponse();
        	dialog.setContent(res);
        	var trade_status = goog.dom.getElement('id_trade_status').value;
        	if (trade_status == 'WAIT_AUDIT'){
        		dialog.setTitle('订单审核详情');
			    dialog.setButtonSet(new goog.ui.Dialog.ButtonSet().addButton({key: 'CHECK', caption: "审核订单"},false,false));
			    goog.events.listen(dialog, goog.ui.Dialog.EventType.SELECT, that);
        	}else{
        		dialog.setTitle('订单重审页面');
        		dialog.setButtonSet(new goog.ui.Dialog.ButtonSet().addButton({key: 'REVIEW', caption: "重审订单"},false,false));
			    goog.events.listen(dialog, goog.ui.Dialog.EventType.SELECT, that);
        	}
		    that.setEvent();
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	}
	goog.net.XhrIo.send('/trades/checkorder/'+id+'/?format=html',callback,'GET');
}

ordercheck.Dialog.prototype.show = function(data) {
    this.dialog.setVisible(true);
    goog.style.setPageOffset(this.dialog.getDialogElement(),this.clickPos);
}

ordercheck.Dialog.prototype.hide = function(data) {
    this.dialog.setVisible(false);
}

//商品搜索事件处理
ordercheck.Dialog.prototype.onProdSearchKeyDown = function(e){
	
	if (e.keyCode==13){
		this.searchProd();	
	}
	return;
}

ordercheck.Dialog.prototype.setEvent=function(){
	var addrBtn = goog.dom.getElement("addr-from-submit");
	goog.events.listen(addrBtn, goog.events.EventType.CLICK,this.changeAddr,false,this);
	
	var searchBtn   = goog.dom.getElement("id-search-prod");
	goog.events.listen(searchBtn, goog.events.EventType.CLICK,this.searchProd,false,this); 
	
	var searchInput = goog.dom.getElement("id-search-q");
	goog.events.listen(searchInput, goog.events.EventType.KEYDOWN,this.searchProd,false,this);
	
	var changeOrderBtns = goog.dom.getElementsByClass("change-order");
	for (var i=0;i<changeOrderBtns.length;i++){
		goog.events.listen(changeOrderBtns[i], goog.events.EventType.CLICK,this.changeOrder,false,this);
	}
	
	var deleteOrderBtns = goog.dom.getElementsByClass("delete-order");
	for (var i=0;i<deleteOrderBtns.length;i++){
		goog.events.listen(deleteOrderBtns[i], goog.events.EventType.CLICK,this.deleteOrder,false,this);
	} 
	
	var addr1  = new goog.ui.Zippy('collapseOne', 'addrContent');   
	var order1 = new goog.ui.Zippy('collapseTwo', 'orderContent');    
	
	$('input.order_num').live('keyup',validInputNum);
	$('input.prod_num').live('keyup',validInputNum);
	$('button.change-order').live('click',function(e){
		e.preventDefault();
		updateTotalNum();
	});
}

//修改地址
ordercheck.Dialog.prototype.changeAddr=function(e){
	var trade_id        = goog.dom.getElement('id_check_trade').value;
	var receiver_name   = goog.dom.getElement('id_receiver_name').value;
	var receiver_mobile = goog.dom.getElement('id_receiver_mobile').value;
	var receiver_phone  = goog.dom.getElement('id_receiver_phone').value;
	var receiver_state  = goog.dom.getElement('id_receiver_state').value;
	var receiver_city   = goog.dom.getElement('id_receiver_city').value;
	var receiver_district = goog.dom.getElement('id_receiver_district').value;
	var receiver_address  = goog.dom.getElement('id_receiver_address').value;
	var receiver_zip    = goog.dom.getElement('id_receiver_zip').value;
	
	var params = {'trade_id':trade_id,'receiver_name':receiver_name,'receiver_mobile':receiver_mobile,
			'receiver_phone':receiver_phone,'receiver_state':receiver_state,'receiver_city':receiver_city,
			'receiver_district':receiver_district,'receiver_address':receiver_address,'receiver_zip':receiver_zip};		
	
	var callback = function(e){
		var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
            if (res.code == 0){
            	goog.dom.getElement('id_receiver').innerText = receiver_name;
            	goog.dom.getElement('id_mobile').innerText   = receiver_mobile;
            	goog.dom.getElement('id_phone').innerText    = receiver_phone;
            	goog.dom.getElement('id_zip').innerText      = receiver_zip;
            	goog.dom.getElement('id_address').innerText  = receiver_state+'，'+receiver_city+'，'+receiver_district+'，'+receiver_address;
            }else{
                alert("地址修改失败:"+res.response_error);
            }
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/trades/address/',callback,'POST',content);
}

//查询商品
ordercheck.Dialog.prototype.searchProd=function(e){
	var sch_table = goog.dom.getElement('id-search-table');
	
	goog.style.showElement(sch_table,true);
	var q = goog.dom.getElement('id-search-q').value;
	if (!q){
		return;
	}

	var that = this;
	for(var i=sch_table.rows.length;i>1;i--){
		sch_table.deleteRow(i-1);
	}
	var params = {'q':q};
	var callback = function(e){
		var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
            if (res.code == 0){
            	for(var i=0;i<res.response_content.length;i++){
            		addSearchRow('id-search-table',res.response_content[i]);
            	}
            	var addOrderBtns = goog.dom.getElementsByClass('add-order');
            	for(var i=0;i<addOrderBtns.length;i++){
            		goog.events.listen(addOrderBtns[i], goog.events.EventType.CLICK,that.addOrder,false,that);
            	}
            }else{
                alert("商品查询失败:"+res.response_error);
            }
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/trades/orderplus/?'+content,callback,'GET');
}

//添加订单
ordercheck.Dialog.prototype.addOrder=function(e){
    var that = this;
	var target = e.target;
	var idx    = target.getAttribute('idx');
	var action = target.getAttribute('action');
	var trade_id     = goog.dom.getElement('id_check_trade').value;
	var outer_id     = target.getAttribute('outer_id');
	var sku_outer_id = goog.dom.getElement('id-order-sku-'+idx).value;
	var num          = goog.dom.getElement('id-order-num-'+idx).value;
	var order_type   = null;
	
	if (action=="return"){
		order_type = RETURN_GOODS_TYPE;
	}else if (action=="change"){
		order_type = CHANGE_GOODS_TYPE;
	}else{
		order_type = HANDSEL_TYPE;
	}
	
	var params     = {'trade_id':trade_id,'outer_id':outer_id,'outer_sku_id':sku_outer_id,'num':num,'type':order_type}
	var callback = function(e){
		var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
            if (res.code == 0){
            	addOrderRow('id_trade_order',res.response_content);
				
				updateTotalNum();
				
            	var deleteOrderBtns = goog.dom.getElementsByClass('delete-order');
            	for(var i =0;i<deleteOrderBtns.length;i++){
            		goog.events.removeAll(deleteOrderBtns[i]);
            		goog.events.listen(deleteOrderBtns[i], goog.events.EventType.CLICK,that.deleteOrder,false,that);
            	}
            }else{
                alert("添加失败:"+res.response_error);
            }
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/trades/orderplus/',callback,'POST',content);
}

//修改订单信息
ordercheck.Dialog.prototype.changeOrder=function(e){
	var target  = e.target;
	var idx     = target.getAttribute('idx');
	var order_id     = target.getAttribute('oid');
	var outer_sku_id = goog.dom.getElement('id-select-ordersku-'+idx).value;
	var order_num    = goog.dom.getElement('id-change-order-num-'+idx).value;
	
	var callback = function(e){
		var xhr  = e.target;
        try {
        	var res = xhr.getResponseJson();
            if (res.code == 0){
                var order = res.response_content;
            	var cell  = target.parentElement.parentElement;
            	cell.cells[0].innerHTML = order.id;
            	cell.cells[1].innerHTML = order.outer_id;
            	cell.cells[2].innerHTML = order.title;
            	cell.cells[3].innerHTML = order.sku_properties_name;
            	cell.cells[4].innerHTML = '<input class="order_num" type="text" value="'+order.num+'" size="8" disabled="disabled" />';
            	cell.cells[5].innerHTML = order.price;
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
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	var params = {'outer_sku_id':outer_sku_id,'order_num':order_num};
	var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/trades/order/update/'+order_id+'/',callback,'POST',content);
}

//删除订单
ordercheck.Dialog.prototype.deleteOrder=function(e){
	var target = e.target;
	var row    = target.parentElement.parentElement;
	var rowIndex = row.rowIndex;
	var table    = row.parentElement.parentElement;
	var order_id = target.getAttribute('oid');

	if(!confirm("确定删除订单 "+order_id+" 吗？"))
	{
	    return;
	}
	
	var callback = function(e){
		var xhr  = e.target;
        try {
        	var res = xhr.getResponseJson();
            if (res.code == 0){
            	table.deleteRow(rowIndex);
            	//重新计算数量
            	updateTotalNum();
            }else{
                alert("订单删除失败:"+res.response_error);
            }
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	goog.net.XhrIo.send('/trades/order/delete/'+order_id+'/',callback,'POST');
}

ordercheck.Dialog.prototype.handleEvent= function (e) {
	var action_code = '';
    if (e.key == 'CHECK') {
        action_code = 'check';
    }else if (e.key == 'REVIEW'){
        action_code = 'review';
    }
	var tradeDom  = goog.dom.getElement("id_check_trade");
    var logisticsDom = goog.dom.getElement("id_logistics");
    var priorityDom  = goog.dom.getElement("id_priority");
    var shippingDom  = goog.dom.getElement("id_shipping_type");
    var retval    = this.orderManager.checkorder(tradeDom.value,logisticsDom.value,priorityDom.value,shippingDom.value,action_code);
   	
    return false;
}

goog.provide("ordercheck.Manager");
ordercheck.Manager = function () {
    this.dialog = new ordercheck.Dialog(this);
    this.check_row_idx = null;
    this.buttons = goog.dom.getElementsByClass("check-order");
    for(var i=0;i<this.buttons.length;i++){
        goog.events.listen(this.buttons[i], goog.events.EventType.CLICK, this.showDialog, false, this);
    }
}

ordercheck.Manager.prototype.showDialog = function(e) {
    var elt = e.target;
    var trade_id = elt.getAttribute('trade_id');
    this.dialog.init(trade_id);
    this.dialog.clickPos = goog.style.getPageOffset(elt);
    this.check_row_idx = elt.parentElement.parentElement.rowIndex;
    this.dialog.show(); 
}

ordercheck.Manager.prototype.checkorder = function(trade_id,logistic_code,priority,shipping,action) {
	var that  = this;
    var callback = function(e){
        var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
            if (res.code == 0){
            	that.dialog.hide(false);
            	var result_table = goog.dom.getElement('result_list');
            	result_table.deleteRow(that.check_row_idx);
            	that.check_row_idx = null;
            }else{
                alert("审核失败:"+res.response_error);
            }
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	var params  = {
					'format':'json',
					'logistic_code':logistic_code,
					'priority':priority,
					'shipping_type':shipping,
					'action':action
				};
	var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/trades/checkorder/'+trade_id+'/?format=json',callback,'POST',content);
}



