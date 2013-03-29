goog.provide('refund');

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
	var sku_options   = '<select id="id-order-sku-'+index.toString()+'" style="width:100px;">';
	for(var i=0;i<prod[3].length;i++){
		var sku = prod[3][i];
		sku_options += '<option value="'+sku[0]+'">'+sku[1]+'</option>';
	}
	sku_options += '</select>';
	sku_cell.innerHTML = sku_options;
	
	var num_cell = goog.dom.createElement('td');
	num_cell.innerHTML = '<input id="id-order-num-'+index.toString()+'" type="text" value="1" style="width:25px;" size="2" />';
	
	var price_cell = createDTText(prod[2]);
	
	var reuse_cell = goog.dom.createElement('td');
	reuse_cell.innerHTML = '<input id="id-order-reuse-'+index.toString()+'" type="checkbox" />';
	
	var addbtn_cell = goog.dom.createElement('td');
	addbtn_cell.innerHTML = '<button class="refund-order btn btn-mini btn-success" outer_id="'+prod[0]+'" idx="'+index.toString()+'">添加 +</button>';
	
	row.appendChild(id_cell);
	row.appendChild(outer_id_cell);
	row.appendChild(title_cell);
	row.appendChild(sku_cell);
	row.appendChild(num_cell);
	row.appendChild(price_cell);
	row.appendChild(reuse_cell);
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
	addbtn_cell.innerHTML = '<button class="show-trade-orders btn btn-mini btn-info" style="margin:1px 0;" trade_id="'+trade.id+'">查看订单</button>';
	
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

var addRefundOrderRow  = function(tableID,order){

	var table = goog.dom.getElement(tableID);
	var rowCount = table.rows.length;
    var row = table.insertRow(rowCount);
    var index = rowCount;
    
	var id_cell = createDTText(index+'');
	var tid_cell      = createDTText(order.trade_id);
	var buyer_nick_cell   = createDTText(order.buyer_nick);
	var buyer_mobile_cell = createDTText(order.buyer_mobile);
	var buyer_phone_cell  = createDTText(order.buyer_phone);
	var out_sid_cell      = createDTText(order.out_sid);
	var company_cell  = createDTText(order.company);
	var title_cell    = createDTText(order.title);
	var property_cell = createDTText(order.property);
	var num_cell   = createDTText(order.num+'');
	
	var reuse_cell   = goog.dom.createElement('td');
	if (order.can_reuse){
		reuse_cell.innerHTML = '<img src="/static/admin/img/icon-yes.gif" alt="True">';
	}else{
		reuse_cell.innerHTML = '<img src="/static/admin/img/icon-no.gif" alt="False">';	
	}
	
	var delete_btn_cell = goog.dom.createElement('td');
	delete_btn_cell.innerHTML = '<button class="delete-order btn btn-mini btn-warning" rid="'+order.id.toString()+'">删除</button>';
	
	row.appendChild(id_cell);
	row.appendChild(tid_cell);
	row.appendChild(buyer_nick_cell);
	row.appendChild(buyer_mobile_cell);
	row.appendChild(buyer_phone_cell);
	row.appendChild(out_sid_cell);
	row.appendChild(company_cell);
	row.appendChild(title_cell);
	row.appendChild(property_cell);
	row.appendChild(num_cell);
	row.appendChild(reuse_cell);
	row.appendChild(delete_btn_cell);
}

goog.provide('refund.Manager');
/** @constructor */
refund.Manager = function () {
    this.prod_q   = null;
    this.trade_q  = null;
    this.search_prod_table  = null;
    this.search_trade_table = null;
    this.refund_table = null;
    this.clearBtn     = null;

    this.prod_q   = goog.dom.getElement('id_prod_q');
    this.trade_q  = goog.dom.getElement('id_trade_q');
	this.search_trade_table = goog.dom.getElement('id-trade-search-table');
	this.search_prod_table  = goog.dom.getElement('id-prod-search-table');
	this.refund_table  = goog.dom.getElement('id-refund-table');
	this.clearBtn      = goog.dom.getElement('id_clear_btn');
	this.bindEvent();
}

//商品搜索事件处理
refund.Manager.prototype.onProdSearchKeyDown = function(e){
	
	var prod_qstr = this.prod_q.value;
	if (e.keyCode==13){
		this.showProduct(prod_qstr);	
	}
	return;
}

//显示商品搜索记录
refund.Manager.prototype.showProduct = function (q) {
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
            	
            	var addRefundOrderBtns = goog.dom.getElementsByClass('refund-order');
            	for(var i=0;i<addRefundOrderBtns.length;i++){
            		goog.events.listen(addRefundOrderBtns[i], goog.events.EventType.CLICK,that.addRefundOrder,false,that);
            	}
            }else{
                alert("商品查询失败:"+res.response_error);
            }
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	}
	goog.net.XhrIo.send('/trades/orderplus/?q='+q,callback);
}

//添加退货订单
refund.Manager.prototype.addRefundOrder = function (e) {
	var that   = this;
	var target = e.target;
	var idx    = target.getAttribute('idx');
	var outer_id     = target.getAttribute('outer_id');
	var sku_outer_id = goog.dom.getElement('id-order-sku-'+idx).value;
	var num          = goog.dom.getElement('id-order-num-'+idx).value;
	var reuse  = goog.dom.getElement('id-order-reuse-'+idx).checked;
	
	var memo      = goog.dom.getElement('id-return-memo').value;
	var trade_id  = goog.dom.getElement('id_trade_id').value;
	var buyer_mobile = goog.dom.getElement('id_receiver_mobile').value;
	var buyer_phone  = goog.dom.getElement('id_receiver_phone').value;
	var buyer_nick   = goog.dom.getElement('id_buyer_nick').value;
	var company   = goog.dom.getElement('id_return_company_name').value;
	var out_sid   = goog.dom.getElement('id_return_out_sid').value;
	
    var callback = function(e){
        var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	if (res.code == 0){
            	addRefundOrderRow('id-refund-table',res.response_content);
            	
            	var deleteOrderBtns = goog.dom.getElementsByClass('delete-order',that.return_table);
            	for(var i =0;i<deleteOrderBtns.length;i++){
            		goog.events.removeAll(deleteOrderBtns[i]);
            		goog.events.listen(deleteOrderBtns[i], goog.events.EventType.CLICK,that.deleteOrder,false,that);
            	}
            	showElement(that.refund_table.parentElement);
            }else{
                alert("添加失败:"+res.response_error);
            }
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	}
	var params     = {
		'trade_id':that.tid,'outer_id':outer_id,'outer_sku_id':sku_outer_id,
		'num':num,'can_reuse':reuse,'memo':memo,'trade_id':trade_id,'buyer_nick':buyer_nick,
		'buyer_mobile':buyer_mobile,'buyer_phone':buyer_phone,'out_sid':out_sid,'company':company
		}
	var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/refunds/product/add/?',callback,'POST',content);
}



//订单搜索事件处理
refund.Manager.prototype.onTradeSearchKeyDown = function(e){
	
	var prod_qstr = this.trade_q.value;
	if (e.keyCode==13){
		this.showTrade(prod_qstr);	
	}
	return;
}

//显示交易搜索记录
refund.Manager.prototype.showTrade = function(q){
    this.search_q = q;
    var that      = this;
    if (q==''||q=='undifine'){return;}
    if (q.length>64){alert('搜索字符串不能超过64字');return;};
    
    var callback = function(e){
        var xhr = e.target;
        //try {
        	var res = xhr.getResponseJson();
        	if (res.code == 0){
        		clearTable(that.search_trade_table);
        		
            	for(var i=0;i<res.response_content.length;i++){
            		var trade_dict = res.response_content[i];
            		addSearchTradeRow('id-trade-search-table',trade_dict);
            	}
 
            	var showTradeOrders = goog.dom.getElementsByClass('show-trade-orders');
            	for(var i=0;i<showTradeOrders.length;i++){
            		goog.events.listen(showTradeOrders[i], goog.events.EventType.CLICK,that.showTradeOrderList,false,that);
            	}

            }else{
                alert("订单查询失败:"+res.response_error);
            }
        /**} catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } */
	}
	goog.net.XhrIo.send('/trades/tradeplus/?q='+q,callback,'GET');
}

//显示交易订单列表信息
refund.Manager.prototype.showTradeOrderList = function(e){
	var that = this;
	var target = e.target;
	var trade_id = target.getAttribute('trade_id');
	var params   = { 'trade_id':trade_id };
	
	var callback = function(e){
		var xhr = e.target;
		try{
			var res = xhr.getResponseJson();
        	if (res.code == 0){
				
        		
        		var deleteOrderBtns = goog.dom.getElementsByClass('delete-order');
            	for(var i =0;i<deleteOrderBtns.length;i++){
            		goog.events.removeAll(deleteOrderBtns[i]);
            		goog.events.listen(deleteOrderBtns[i], goog.events.EventType.CLICK,that.deleteOrder,false,that);
            	}
            	showElement(that.return_table.parentElement);
            	showElement(that.change_table.parentElement);
        	}else{
                alert("加退货单失败:"+res.response_error);
            }
		} catch (err) {
            console.log('Error: (ajax callback) - ', err);
        }
	}
	var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/trades/tradeplus/?',callback,'POST',content); 
}

//将交易订单加入退回商品清单
refund.Manager.prototype.addTradeOrder = function(e){
	var that = this;
	var target = e.target;
	var cp_tid = target.getAttribute('trade_id');
	var action = target.getAttribute('action');
	var gift_type = null;
	if (action=="return"){
		gift_type = RETURN_GOODS_TYPE;
	}else{
		gift_type = CHANGE_GOODS_TYPE;
	}
	
	var callback = function(e){
		var xhr = e.target;
		try{
			var res = xhr.getResponseJson();
        	if (res.code == 0){
        		clearTable(that.return_table);
        		clearTable(that.change_table);
        		
        		var trade_list = res.response_content;
        		//将订单加入退货单列表
        		
        		var deleteOrderBtns = goog.dom.getElementsByClass('delete-order');
            	for(var i =0;i<deleteOrderBtns.length;i++){
            		goog.events.removeAll(deleteOrderBtns[i]);
            		goog.events.listen(deleteOrderBtns[i], goog.events.EventType.CLICK,that.deleteOrder,false,that);
            	}
            	showElement(that.return_table.parentElement);
            	showElement(that.change_table.parentElement);
        	}else{
                alert("加退货单失败:"+res.response_error);
            }
		} catch (err) {
            console.log('Error: (ajax callback) - ', err);
        }
	}
    var params = {'pt_tid':that.tid,'cp_tid':cp_tid,'type':gift_type};
    var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/trades/tradeplus/?',callback,'POST',content); 
}


//删除订单
refund.Manager.prototype.deleteOrder = function(e){
	var target = e.target;
	var row    = target.parentElement.parentElement;
	var rowIndex = row.rowIndex;
	var table    = row.parentElement.parentElement;
	var rid = target.getAttribute('rid');
	var callback = function(e){
		var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
            if (res.code == 0){
            	table.deleteRow(rowIndex);
            }else{
                alert("错误:"+res.response_error);
            }
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	goog.net.XhrIo.send('/refunds/product/del/'+rid+'/',callback,'GET');
}


//清除基本信息表格
refund.Manager.prototype.clearPanel = function(e){
	goog.dom.getElement('id-return-memo').value='';
	goog.dom.getElement('id_trade_id').value='';
	goog.dom.getElement('id_receiver_mobile').value='';
	goog.dom.getElement('id_receiver_phone').value='';
	goog.dom.getElement('id_buyer_nick').value='';
	goog.dom.getElement('id_return_company_name').value='';
	goog.dom.getElement('id_return_out_sid').value='';
}


//绑定事件
refund.Manager.prototype.bindEvent = function () {

	goog.events.listen(this.prod_q, goog.events.EventType.KEYDOWN,this.onProdSearchKeyDown,false,this);
	goog.events.listen(this.trade_q, goog.events.EventType.KEYDOWN,this.onTradeSearchKeyDown,false,this);
	
	goog.events.listen(this.prod_q, goog.events.EventType.FOCUS,this.focus,false,this);
	goog.events.listen(this.trade_q, goog.events.EventType.FOCUS,this.focus,false,this);
	
	goog.events.listen(this.clearBtn, goog.events.EventType.CLICK,this.clearPanel,false,this);
	var returns_zippy  = new goog.ui.Zippy('id-refund-head', 'id-refund-goods');   
}

refund.Manager.prototype.focus = function(e){
	var target = e.target;
	if (target==this.prod_q){
		showElement(this.search_prod_table.parentElement);
		hideElement(this.search_trade_table.parentElement);
	}else if (target==this.trade_q){
		showElement(this.search_trade_table.parentElement);
		hideElement(this.search_prod_table.parentElement);
	}
	
}

