goog.provide('exchange');

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
	addbtn_cell.innerHTML = '<button class="return-order btn-mini" outer_id="'+prod[0]+'" idx="'+index.toString()+'">退货</button>'
							+'&nbsp;<button class="change-order btn-mini" outer_id="'+prod[0]+'" idx="'+index.toString()+'">换货</button>';
	
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
    
	var id_cell = createDTText(index.toString());
	var buyer_nick_cell   = createDTText(trade.buyer_nick);
	var num_cell     = createDTText(trade.total_num.toString());
	var pay_time_cell     = createDTText(trade.pay_time);
	var consign_time_cell = createDTText(trade.consign_time);
	var receiver_cell     = createDTText(trade.receiver_name);
	var address_cell      = createDTText(trade.receiver_state+','+trade.receiver_city
		+','+trade.receiver_district+','+trade.receiver_address);
	
	var mobile_cell = createDTText(trade.receiver_mobile);
	var phone_cell  = createDTText(trade.receiver_phone);
	var addbtn_cell = goog.dom.createElement('td');
	addbtn_cell.innerHTML = '<button class="trade-buyer-info btn-mini" outer_id="'+trade.id+'" idx="'+index.toString()+'">复制用户</button>'
							+'&nbsp;<button class="trade-return-order btn-mini" outer_id="'+trade.id+'" idx="'+index.toString()+'">加退货单</button>'
							+'&nbsp;<button class="trade-change-order btn-mini" outer_id="'+trade.id+'" idx="'+index.toString()+'">加换货单</button>';
	
	row.appendChild(id_cell);
	row.appendChild(buyer_nick_cell);
	row.appendChild(num_cell);
	row.appendChild(pay_time_cell);
	row.appendChild(consign_time_cell);
	row.appendChild(receiver_cell);
	row.appendChild(address_cell);
	row.appendChild(mobile_cell);	
	row.appendChild(phone_cell);	
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

	var num_cell = createDTText(order.num+'');
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
}

goog.provide('exchange.Manager');
/** @constructor */
exchange.Manager = function () {
    this.prod_q   = null;
    this.trade_q  = null;
    this.search_prod_table  = null;
    this.search_trade_table = null;
    this.return_table = null;
    this.change_table = null;
    
    this.prod_q   = goog.dom.getElement('id_prod_q');
    this.trade_q  = goog.dom.getElement('id_trade_q');
	this.search_trade_table = goog.dom.getElement('id-trade-search-table');
	this.search_prod_table  = goog.dom.getElement('id-prod-search-table');
	this.return_table = goog.dom.getElement('id-return-table');
	this.change_table = goog.dom.getElement('id-change-table');

	this.bindEvent();
}

exchange.Manager.prototype.onProdSearchKeyDown = function(e){
	
	var prod_qstr = this.prod_q.value;
	if (e.keyCode==13){
		this.showProduct(prod_qstr);	
	}
	return;
}

//显示商品搜索记录
exchange.Manager.prototype.showProduct = function (q) {
	this.search_q = q;
    var that      = this;
    if (q==''||q=='undifine'){return;}
    if (q.length>40){alert('搜索字符串不能超过40字');return;};
    
    for(var i=this.search_prod_table.rows.length;i>1;i--){
		this.search_prod_table.deleteRow(i-1);
	}
    var callback = function(e){
        var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	if (res.code == 0){
            	for(var i=0;i<res.response_content.length;i++){
            		addSearchProdRow('id-prod-search-table',res.response_content[i]);
            	}
            	
            	var addReturnOrderBtns = goog.dom.getElementsByClass('return-order');
            	for(var i=0;i<addReturnOrderBtns.length;i++){
            		goog.events.listen(addReturnOrderBtns[i], goog.events.EventType.CLICK,that.addReturnOrder,false,that);
            	}
            	
            	var addChangeOrderBtns = goog.dom.getElementsByClass('change-order');
            	for(var i=0;i<addChangeOrderBtns.length;i++){
            		goog.events.listen(addChangeOrderBtns[i], goog.events.EventType.CLICK,that.addChangeOrder,false,that);
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

//添加退货订单
exchange.Manager.prototype.addReturnOrder = function (e) {
	var that   = this;
	var target = e.target;
	var idx    = target.getAttribute('idx');
    var trade_id     = goog.dom.getElement('id_exchange_trade').value;
	var outer_id     = target.getAttribute('outer_id');
	var sku_outer_id = goog.dom.getElement('id-order-sku-'+idx).value;
	var num          = goog.dom.getElement('id-order-num-'+idx).value;
	var params     = {'trade_id':trade_id,'outer_id':outer_id,'outer_sku_id':sku_outer_id,'num':num}
	
    var callback = function(e){
        var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	if (res.code == 0){
            	addOrderRow('id-return-table',res.response_content);
            	var deleteOrderBtns = that.return_table.getElementsByClass('delete-order');
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
	}
	var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/trades/orderplus/?',callback,'POST',content);
}

//添加换货订单
exchange.Manager.prototype.addChangeOrder = function (e) {
	var that   = this;
	var target = e.target;
	var idx    = target.getAttribute('idx');
    var trade_id     = goog.dom.getElement('id_exchange_trade').value;
	var outer_id     = target.getAttribute('outer_id');
	var sku_outer_id = goog.dom.getElement('id-order-sku-'+idx).value;
	var num          = goog.dom.getElement('id-order-num-'+idx).value;
	var params     = {'trade_id':trade_id,'outer_id':outer_id,'outer_sku_id':sku_outer_id,'num':num}
	
    var callback = function(e){
        var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	if (res.code == 0){
            	addOrderRow('id-change-table',res.response_content);
            	var deleteOrderBtns = that.change_table.getElementsByClass('delete-order');
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
	}
	var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/trades/orderplus/?',callback,'POST',content);
}

exchange.Manager.prototype.onTradeSearchKeyDown = function(e){
	
	var prod_qstr = this.trade_q.value;
	if (e.keyCode==13){
		this.showTrade(prod_qstr);	
	}
	return;
}

//显示交易搜索记录
exchange.Manager.prototype.showTrade = function(q){
	this.search_q = q;
    var that   = this;
    var callback = function(e){
        var xhr = e.target;
        //try {
        	var res = xhr.getResponseJson();
        	if (res.code == 0){
            	for(var i=0;i<res.response_content.length;i++){
            		console.log(res.response_content[i]);
            		addSearchTradeRow('id-trade-search-table',res.response_content[i]);
            	}
            	
            }else{
                alert("订单查询失败:"+res.response_error);
            }
        //} catch (err) {
        //    console.log('Error: (ajax callback) - ', err);
        //} 
	}
	goog.net.XhrIo.send('/trades/tradeplus/?q='+q,callback,'GET');
}

//删除订单
exchange.Manager.prototype.deleteOrder = function(e){
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
exchange.Manager.prototype.bindEvent = function () {

	goog.events.listen(this.prod_q, goog.events.EventType.KEYDOWN,this.onProdSearchKeyDown,false,this);
	goog.events.listen(this.trade_q, goog.events.EventType.KEYDOWN,this.onTradeSearchKeyDown,false,this);
	
	goog.events.listen(this.prod_q, goog.events.EventType.FOCUS,this.focus,false,this);
	goog.events.listen(this.trade_q, goog.events.EventType.FOCUS,this.focus,false,this);

	
	var returns_zippy  = new goog.ui.Zippy('id-return-head', 'id-return-goods');   
	var changes_zippy  = new goog.ui.Zippy('id-change-head', 'id-change-goods');
}

exchange.Manager.prototype.focus = function(e){
	var target = e.target;
	if (target==this.prod_q){
		showElement(this.search_prod_table.parentElement);
		hideElement(this.search_trade_table.parentElement);
	}else if (target==this.trade_q){
		showElement(this.search_trade_table.parentElement);
		hideElement(this.search_prod_table.parentElement);
	}
	
}

