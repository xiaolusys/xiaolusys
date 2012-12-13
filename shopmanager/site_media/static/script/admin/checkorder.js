goog.provide('ordercheck');
goog.provide('ordercheck.Dialog');

goog.require('goog.dom');
goog.require('goog.ui.Dialog');
goog.require('goog.style');

goog.require('goog.net.XhrIo');
goog.require('goog.uri.utils');

var createDTText  = function(text){
	var td = goog.dom.createElement('td');
	td.appendChild(goog.dom.createTextNode(text));
	return td
}

/** @constructor */
ordercheck.Dialog = function (manager) {
    this.dialog = new goog.ui.Dialog();
    this.orderManager = manager;
    this.trade_id = null; 
}

ordercheck.Dialog.prototype.init = function (id) {
	dialog = this.dialog ;
    that   = this ;
    var callback = function(e){
        var xhr = e.target;
        try {
        	var res = xhr.getResponse();
        	dialog.setContent(res);
		    dialog.setTitle('订单审核详情');
		    dialog.setButtonSet(new goog.ui.Dialog.ButtonSet().addButton({key: 'OK', caption: "审核订单"}
		        ,true,false));
		    goog.events.listen(dialog, goog.ui.Dialog.EventType.SELECT, that);
		    that.setEvent();
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	}
	goog.net.XhrIo.send('/trades/checkorder/'+id+'/?format=html',callback,'GET')
}

ordercheck.Dialog.prototype.show = function(data) {
    this.dialog.setVisible(true);
}

ordercheck.Dialog.prototype.setEvent=function(){
	var addrBtn = goog.dom.getElement("addr-from-submit");
	goog.events.listen(addrBtn, goog.events.EventType.CLICK,this.changeAddr,false,this);
	
	var searchBtn = goog.dom.getElement("id-search-prod");
	goog.events.listen(searchBtn, goog.events.EventType.CLICK,this.searchProd,false,this); 
	
	var changeOrderBtns = goog.dom.getElementsByClass("change-order");
	for (var i=0;i<changeOrderBtns.length;i++){
		goog.events.listen(changeOrderBtns[i], goog.events.EventType.CLICK,this.changeOrder,false,this);
	}
	
	var deleteOrderBtns = goog.dom.getElementsByClass("delete-order");
	for (var i=0;i<deleteOrderBtns.length;i++){
		goog.events.listen(deleteOrderBtns[i], goog.events.EventType.CLICK,this.deleteOrder,false,this);
	}                                                                                                                                                                                                                                               
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
	
	params = {'trade_id':trade_id,'receiver_name':receiver_name,'receiver_mobile':receiver_mobile,'receiver_phone':receiver_phone,
			'receiver_state':receiver_state,'receiver_city':receiver_city,'receiver_district':receiver_district,'receiver_address':receiver_address}		
	
	var callback = function(e){
		var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
            if (res.code == 0){
            	alert("地址修改成功！");
            }else{
                alert("地址修改失败:"+res.response_error);
            }
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/trades/address/',callback,'POST',content);
}

//查询商品
ordercheck.Dialog.prototype.searchProd=function(e){
	var q = goog.dom.getElement('id-search-q').value;
	var sch_table = goog.dom.getElement('id-search-table');
	for(var i=1;i<sch_table.rows.length;i++){
		sch_table.deleteRow(i);
	}
	params = {'q':q}
	var callback = function(e){
		var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
            if (res.code == 0){
            	console.log(res);
            	for(var i=0;i<res.response_content.length;i++){
            		index = i+1;
            		var prod = res.response_content[i];
            		var tr = goog.dom.createElement('tr');
            		var id_cell = createDTText(index+'');
            		var outer_id_cell = createDTText(prod[0]);
            		var title_cell    = createDTText(prod[1]);
            		
            		var sku_cell = goog.dom.createElement('td');
            		var sku_options = '<select id="id-order-sku-'+index.toString()+'" >';
            		for(var i=0;i<prod[3].length;i++){
            			var sku = prod[3][i];
            			sku_options += '<option value="'+sku[0]+'">'+sku[1]+'</option>';
            		}
            		sku_options += '</select>';
            		sku_cell.innerHTML = sku_options;
            		
            		var num_cell = goog.dom.createElement('td');
            		num_cell.innerHTML = '<input id="id-order-num-'+index.toString()+'" type="text" size="2" />';
            		
            		var price_cell = createDTText(prod[2]);
            		
            		var addbtn_cell = goog.dom.createElement('td');
            		addbtn_cell.innerHTML = '<input class="add-order" idx="'+index.toString()+'" type="button" />';
            		
            		tr.appendChild(id_cell);
            		tr.appendChild(outer_id_cell);
            		tr.appendChild(title_cell);
            		tr.appendChild(sku_cell);
            		tr.appendChild(num_cell);
            		tr.appendChild(price_cell);
            		tr.appendChild(addbtn_cell);
            		sch_table.appendChild(tr);
            	}
            }else{
                alert("地址修改失败:"+res.response_error);
            }
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/trades/orderplus/?'+content,callback,'GET');
}

//添加订单
ordercheck.Dialog.prototype.addOrder=function(e){
	var q = goog.dom.getElement('id-search-q').value;
	params = {'q':q}
	var callback = function(e){
		var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	console.log('debug search:',res);
            if (res.code == 0){
            	alert("地址修改成功！");
            }else{
                alert("地址修改失败:"+res.response_error);
            }
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/trades/orderplus/?'+content,callback,'GET');
}

//修改订单信息
ordercheck.Dialog.prototype.changeOrder=function(e){
	var q = goog.dom.getElement('id-search-q').value;
	params = {'q':q}
	var callback = function(e){
		var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	console.log('debug search:',res);
            if (res.code == 0){
            	alert("地址修改成功！");
            }else{
                alert("地址修改失败:"+res.response_error);
            }
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/trades/orderplus/?'+content,callback,'GET');
}

//删除订单
ordercheck.Dialog.prototype.deleteOrder=function(e){
	var q = goog.dom.getElement('id-search-q').value;
	params = {'q':q}
	var callback = function(e){
		var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	console.log('debug search:',res);
            if (res.code == 0){
            	alert("地址修改成功！");
            }else{
                alert("地址修改失败:"+res.response_error);
            }
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/trades/orderplus/?'+content,callback,'GET');
}

ordercheck.Dialog.prototype.handleEvent= function (e) {
    if (e.key == 'OK') {
        var tradeDom  = goog.dom.getElement("id_check_trade");
        var logisticsDom = goog.dom.getElement("id_logistics");
        var priorityDom  = goog.dom.getElement("id_priority");
        var retval    = this.orderManager.checkorder(tradeDom.value, logisticsDom.value, priorityDom.value);
    }
    return false;
}


goog.provide("ordercheck.Manager");
ordercheck.Manager = function () {
    this.dialog = new ordercheck.Dialog(this);
    this.buttons = goog.dom.getElementsByClass("check-order");
    for(var i=0;i<this.buttons.length;i++){
        goog.events.listen(this.buttons[i], goog.events.EventType.CLICK, this.showDialog, false, this);
    }
}

ordercheck.Manager.prototype.showDialog = function(e) {
    var elt = e.target;
    trade_id = elt.getAttribute('trade_id')
    this.dialog.init(trade_id);
    this.dialog.show(); 
}

ordercheck.Manager.prototype.checkorder = function(trade_id,logistic_code,priority) {
    var callback = function(e){
        var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
            if (res.code == 0){
            	alert("审核成功！");
            }else{
                alert("审核失败:"+res.response_error);
            }
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	params  = {'format':'json','logistic_code':logistic_code,'priority':priority};
	content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/trades/checkorder/'+trade_id+'/',callback,'POST',content);
}


new ordercheck.Manager()
