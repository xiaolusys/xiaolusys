goog.provide('direct');

goog.require('goog.dom');
goog.require('goog.ui.Dialog');
goog.require('goog.ui.Zippy');
goog.require('goog.style');
goog.require('goog.ui.Component.EventType');

goog.require('goog.net.XhrIo');
goog.require('goog.uri.utils');

//添加商品搜索结果
var addSearchProdRow  = function(tableID,prod){

	var table = goog.dom.getElement(tableID);
	var rowCount = table.rows.length;
    var row   = table.insertRow(rowCount);
    var index = rowCount;
    
	var id_cell = createDTText(index+'');
	var outer_id_cell = createDTText(prod[0]);
	var title_cell    = createDTText(prod[1]);
	var sku_cell      = goog.dom.createElement('td');
	var sku_options   = '<select id="id-order-sku-'+index.toString()+'" >';
	for(var i=0;i<prod[3].length;i++){
		var sku = prod[3][i];
		sku_options += '<option value="'+sku[0]+'">'+sku[1]+'</option>';
	}
	sku_options += '</select>';
	sku_cell.innerHTML = sku_options;
	
	var num_cell = goog.dom.createElement('td');
	num_cell.innerHTML = '<input id="id-order-num-'+index.toString()+'" type="text" value="1" style="width:25px;" size="2" />';
	
	var price_cell = createDTText(prod[2]);
	
	var addbtn_cell = goog.dom.createElement('td');
	addbtn_cell.innerHTML = '<button class="add-order btn btn-mini btn-success" outer_id="'+prod[0]+'" idx="'+index.toString()+'">添加</button>';
	
	row.appendChild(id_cell);
	row.appendChild(outer_id_cell);
	row.appendChild(title_cell);
	row.appendChild(sku_cell);
	row.appendChild(num_cell);
	row.appendChild(price_cell);
	row.appendChild(addbtn_cell);	
}

//添加订单搜索结果
var addSearchTradeRow  = function(tableID,trade){

	var table = goog.dom.getElement(tableID);
	var rowCount = table.rows.length;
    var row   = table.insertRow(rowCount);
    var index = rowCount;
    
	var id_cell = createDTText(index+'');
	var buyer_nick_cell   = createDTText(trade.buyer_nick);
	var num_cell     = createDTText(trade.total_num+'');
	var pay_time_cell     = createDTText(trade.pay_time);
	var consign_time_cell = createDTText(trade.consign_time);
	var receiver_cell     = createDTText(trade.receiver_name);
	var address_cell      = createDTText(trade.receiver_state+','+trade.receiver_city
		+','+trade.receiver_district+','+trade.receiver_address+','
		+trade.receiver_mobile+','+trade.receiver_phone+','+trade.receiver_zip);
	
	var status_cell = createDTText(trade.status);
	var sys_status_cell  = createDTText(trade.sys_status);
	var addbtn_cell = goog.dom.createElement('td');
	addbtn_cell.innerHTML = '<button class="copy-trade-buyer-info btn btn-mini btn-info" style="margin:1px 0;" trade_id="'+trade.id+'">复制用户</button>'
							+'<br> <button class="copy-trade-order btn btn-mini btn-success" style="margin:1px 0;" action="direct" trade_id="'+trade.id+'">复制订单</button>';
	
	row.appendChild(id_cell);
	row.appendChild(buyer_nick_cell);
	row.appendChild(num_cell);
	row.appendChild(pay_time_cell);
	row.appendChild(consign_time_cell);
	row.appendChild(receiver_cell);
	row.appendChild(address_cell);
	row.appendChild(status_cell);	
	row.appendChild(sys_status_cell);	
	row.appendChild(addbtn_cell);	
}

var addOrderRow  = function(tableID,order){

	var table = goog.dom.getElement(tableID);
	var rowCount = table.rows.length;
    var row = table.insertRow(rowCount);
    
	var id_order_cell = createDTText(order.id+'');
	var outer_id_cell = createDTText(order.outer_id);
	var title_cell    = createDTText(order.title);
	var sku_properties_name_cell = createDTText(order.sku_properties_name);

	var num_cell   = createDTText(order.num+'');
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
	delete_btn_cell.innerHTML = '<button class="delete-order btn-mini btn-warning" oid="'+order.id.toString()+'">删除</button>';
	
	row.appendChild(id_order_cell);
	row.appendChild(outer_id_cell);
	row.appendChild(title_cell);
	row.appendChild(sku_properties_name_cell);
	row.appendChild(num_cell);
	row.appendChild(price_cell);
	row.appendChild(stock_status_cell);
	row.appendChild(gift_type_cell);
	row.appendChild(delete_btn_cell);
}

goog.provide('direct.Manager');
/** @constructor */
direct.Manager = function () {
    this.prod_q   = null;
    this.trade_q  = null;
    this.search_prod_table  = null;
    this.search_trade_table = null;
    this.return_table = null;
    this.saveBtn      = null;
	this.tid     = null
    this.trades_dict   = {};
    
    this.prod_q   = goog.dom.getElement('id_prod_q');
    this.trade_q  = goog.dom.getElement('id_trade_q');
	this.search_trade_table = goog.dom.getElement('id-trade-search-table');
	this.search_prod_table  = goog.dom.getElement('id-prod-search-table');
	this.return_table = goog.dom.getElement('id-return-table');
	this.saveBtn      = goog.dom.getElement('id_save_trade');
	this.tid     = goog.dom.getElement('id_direct_trade').value;
	this.bindEvent();
}

//商品搜索事件处理
direct.Manager.prototype.onProdSearchKeyDown = function(e){
	
	var prod_qstr = this.prod_q.value;
	if (e.keyCode==13){
		this.showProduct(prod_qstr);	
	}
	return;
}

//显示商品搜索记录
direct.Manager.prototype.showProduct = function (q) {
	this.search_q = q;
    var that      = this;
    if (q==''||q=='undifine'){return;}
    if (q.length>40){alert('搜索字符串不能超过40字');return;};

    var callback = function(e){
        var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	if (res.code == 0){
        		clearTable(that.search_prod_table);
        		
            	for(var i=0;i<res.response_content.length;i++){
            		addSearchProdRow('id-prod-search-table',res.response_content[i]);
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
	}
	goog.net.XhrIo.send('/trades/orderplus/?q='+q,callback,'GET');
}

//添加订单
direct.Manager.prototype.addOrder = function (e) {
	var that   = this;
	var target = e.target;
	var idx    = target.getAttribute('idx');
	var outer_id     = target.getAttribute('outer_id');
	var sku_outer_id = goog.dom.getElement('id-order-sku-'+idx).value;
	var num          = goog.dom.getElement('id-order-num-'+idx).value;

    var callback = function(e){
        var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	if (res.code == 0){
            	addOrderRow('id-return-table',res.response_content);
            	
            	var deleteOrderBtns = goog.dom.getElementsByClass('delete-order',that.return_table);
            	for(var i =0;i<deleteOrderBtns.length;i++){
            		goog.events.removeAll(deleteOrderBtns[i]);
            		goog.events.listen(deleteOrderBtns[i], goog.events.EventType.CLICK,that.deleteOrder,false,that);
            	}
            	showElement(that.return_table.parentElement);
            }else{
                alert("添加失败:"+res.response_error);
            }
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	}
	var params     = {'trade_id':that.tid,'outer_id':outer_id,'outer_sku_id':sku_outer_id,'num':num,'type':HANDSEL_TYPE}
	var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/trades/orderplus/?',callback,'POST',content);
}


//订单搜索事件处理
direct.Manager.prototype.onTradeSearchKeyDown = function(e){
	
	var prod_qstr = this.trade_q.value;
	if (e.keyCode==13){
		this.showTrade(prod_qstr);	
	}
	return;
}

//显示交易搜索记录
direct.Manager.prototype.showTrade = function(q){
    this.search_q = q;
    var that      = this;
    if (q==''||q=='undifine'){return;}
    if (q.length>64){alert('搜索字符串不能超过64字');return;};
    
    var callback = function(e){
        var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	if (res.code == 0){
        		clearTable(that.search_trade_table);
        		
            	for(var i=0;i<res.response_content.length;i++){
            		var trade_dict = res.response_content[i];
            		addSearchTradeRow('id-trade-search-table',trade_dict);
            		that.trades_dict[trade_dict['id']] = trade_dict;
            	}
 
            	var copyBuyerInfoBtns = goog.dom.getElementsByClass('copy-trade-buyer-info');
            	for(var i=0;i<copyBuyerInfoBtns.length;i++){
            		goog.events.listen(copyBuyerInfoBtns[i], goog.events.EventType.CLICK,that.copyBuyerInfo,false,that);
            	}
            	
            	var addToReturnBtns = goog.dom.getElementsByClass('copy-trade-order');
            	for(var i=0;i<addToReturnBtns.length;i++){
            		goog.events.listen(addToReturnBtns[i], goog.events.EventType.CLICK,that.addTradeOrder,false,that);
            	}
            	

            }else{
                alert("订单查询失败:"+res.response_error);
            }
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	}
	goog.net.XhrIo.send('/trades/tradeplus/?q='+q,callback,'GET');
}


//将交易订单加入内售单
direct.Manager.prototype.addTradeOrder = function(e){
	var that = this;
	var target = e.target;
	var cp_tid = target.getAttribute('trade_id');

	var callback = function(e){
		var xhr = e.target;
		try{
			var res = xhr.getResponseJson();
        	if (res.code == 0){
        		clearTable(that.return_table);
        		
        		var trade_list = res.response_content;
        		for(var i=0;i<trade_list.length;i++){
        			var trade = trade_list[i];
        			addOrderRow('id-return-table',trade);
        		}
        		
        		var deleteOrderBtns = goog.dom.getElementsByClass('delete-order');
            	for(var i =0;i<deleteOrderBtns.length;i++){
            		goog.events.removeAll(deleteOrderBtns[i]);
            		goog.events.listen(deleteOrderBtns[i], goog.events.EventType.CLICK,that.deleteOrder,false,that);
            	}
            	showElement(that.return_table.parentElement);
        	}else{
                alert("加内售单失败:"+res.response_error);
            }
		} catch (err) {
            console.log('Error: (ajax callback) - ', err);
        }
	}
    var params = {'pt_tid':that.tid,'cp_tid':cp_tid,'type':HANDSEL_TYPE};
    var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/trades/tradeplus/?',callback,'POST',content);
    
}

//复制订单用户信息
direct.Manager.prototype.copyBuyerInfo = function(e){
	var target = e.target;
	var trade_id    = target.getAttribute('trade_id');
    if (trade_id in this.trades_dict){
    	var trade_dict = this.trades_dict[trade_id];
    	goog.dom.getElement('id_seller_id').value  = trade_dict.seller_id.toString();
    	goog.dom.getElement('id_buyer_nick').value = trade_dict.buyer_nick;
    	goog.dom.getElement('id_receiver_mobile').value = trade_dict.receiver_mobile;
    	goog.dom.getElement('id_receiver_phone').value = trade_dict.receiver_phone;
    	goog.dom.getElement('id_receiver_name').value = trade_dict.receiver_name;
    	goog.dom.getElement('id_receiver_state').value = trade_dict.receiver_state;
    	goog.dom.getElement('id_receiver_city').value = trade_dict.receiver_city;
    	goog.dom.getElement('id_receiver_district').value = trade_dict.receiver_district;
    	goog.dom.getElement('id_receiver_address').value = trade_dict.receiver_address;
    }
}


//删除订单
direct.Manager.prototype.deleteOrder = function(e){
	var target = e.target;
	var row    = target.parentElement.parentElement;
	var rowIndex = row.rowIndex;
	var table    = row.parentElement.parentElement;
	var order_id = target.getAttribute('oid');
	var callback = function(e){
		var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
            if (res.code == 0){
            	table.deleteRow(rowIndex);
            }else{
                alert("订单删除失败:"+res.response_error);
            }
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	goog.net.XhrIo.send('/trades/order/delete/'+order_id+'/',callback,'POST');
}


//绑定事件
direct.Manager.prototype.bindEvent = function () {

	goog.events.listen(this.prod_q, goog.events.EventType.KEYDOWN,this.onProdSearchKeyDown,false,this);
	goog.events.listen(this.trade_q, goog.events.EventType.KEYDOWN,this.onTradeSearchKeyDown,false,this);
	
	goog.events.listen(this.prod_q, goog.events.EventType.FOCUS,this.focus,false,this);
	goog.events.listen(this.trade_q, goog.events.EventType.FOCUS,this.focus,false,this);

	
	var returns_zippy  = new goog.ui.Zippy('id-return-head', 'id-return-goods');   
}

direct.Manager.prototype.focus = function(e){
	var target = e.target;
	if (target==this.prod_q){
		showElement(this.search_prod_table.parentElement);
		hideElement(this.search_trade_table.parentElement);
	}else if (target==this.trade_q){
		showElement(this.search_trade_table.parentElement);
		hideElement(this.search_prod_table.parentElement);
	}
	
}

