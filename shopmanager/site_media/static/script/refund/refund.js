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
	sku_options += '<option value="">--------</option>';
	for(var i=0;i<prod[3].length;i++){
		var sku = prod[3][i];
		sku_options += '<option value="'+sku[0]+'">'+sku[1]+'</option>';
	}
	sku_options += '</select>';
	sku_cell.innerHTML = sku_options;
	
	var price_cell = createDTText(prod[2]);
	
	var addbtn_cell = goog.dom.createElement('td');
	addbtn_cell.innerHTML = '<button class="refund-order-add btn btn-mini btn-primary" title="'+prod[1]
		+'" outer_id="'+prod[0]+'" idx="'+index.toString()+'">添加 +</button>';
	
	row.appendChild(id_cell);		
	row.appendChild(outer_id_cell); 
	row.appendChild(title_cell);	 
	row.appendChild(sku_cell);		 
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

//添加确认订单信息列表
var addFirmOrderRow  = function(tableID,order){

	var table = goog.dom.getElement(tableID);
	var rowCount = table.rows.length;
    var row = table.insertRow(rowCount);
    var index = rowCount;

	var tid_cell      = createDTText(order.trade_id);
	var buyer_nick_cell   = createDTText(order.buyer_nick);
	var buyer_mobile_cell = createDTText(order.buyer_mobile);
	var buyer_phone_cell  = createDTText(order.buyer_phone);
	var out_sid_cell      = createDTText(order.out_sid);
	var company_cell  = createDTText(order.company);
	var title_cell    = createDTText(order.title);
	var property_cell = createDTText(order.property);
	
	var num_cell   = goog.dom.createElement('td');
	num_cell.innerHTML = '<input id="id-confirm-num-'+index.toString()+'" type="text" style="width:20px;" value="1" />';
	
	var reuse_cell   = goog.dom.createElement('td');
	reuse_cell.innerHTML = '<input id="id-reuse-'+index.toString()+'" type="checkbox"  >';
	
	var confirm_btn_cell = goog.dom.createElement('td');
	confirm_btn_cell.innerHTML = '<button class="confirm-order btn btn-mini btn-success" idx="'+index.toString()+'">确认</button>';
	
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
	row.appendChild(confirm_btn_cell);
}

var addRefundOrderRow  = function(tableID,order){

	var table = goog.dom.getElement(tableID);
	var rowCount = table.rows.length;
    var row = table.insertRow(rowCount);
    var index = rowCount;
    
	var id_cell = createDTText(index+'');
	var tid_cell      = createDTText(order.trade_id!=''?order.trade_id:'-');
	var buyer_nick_cell   = createDTText(order.buyer_nick!=''?order.buyer_nick:'-');
	var buyer_mobile_cell = createDTText(order.buyer_mobile!=''?order.buyer_mobile:'-');
	var buyer_phone_cell  = createDTText(order.buyer_phone!=''?order.buyer_phone:'-');
	var out_sid_cell      = createDTText(order.out_sid!=''?order.out_sid:'-');
	var company_cell  = createDTText(order.company!=''?order.company:'-');
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

//子订单列表显示对话框
goog.provide('refund.OrderListDialog');
refund.OrderListDialog = function(manager){
	this.refundManager = manager;
	this.promptDiv     = goog.dom.getElement('order-prompt');
	this.promptBody    = goog.dom.getElement('order-prompt-body');
	this.trade_id      = null;
	
	var closeBtn  = goog.dom.getElement('prompt-close');
	goog.events.listen(closeBtn, goog.events.EventType.CLICK,this.hide,false,this);
}

refund.OrderListDialog.prototype.init = function(id){
	this.trade_id = id;
	var that = this;
	var callback = function(e){
		var xhr = e.target;
        try {
        	var res = xhr.getResponse();
        	that.promptBody.innerHTML = res;
        	var addRefundBtns = goog.dom.getElementsByClass('order-list-add');
        	for(var i=0;i<addRefundBtns.length;i++){
        		goog.events.listen(addRefundBtns[i], goog.events.EventType.CLICK,that.refundManager.addRefundOrder,false,that.refundManager);
        	}
        	that.show();
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        }
	}
	goog.net.XhrIo.send('/trades/order/list/'+id+'/?format=html',callback,'GET');
}

refund.OrderListDialog.prototype.show = function(){
	var trade_search_dialog = goog.dom.getElement('id-trade-search-dialog');
	var pos = goog.style.getPageOffset(trade_search_dialog);
	goog.style.setPageOffset(this.promptDiv,pos);
	goog.style.setStyle(this.promptDiv, "display", "block");
}

refund.OrderListDialog.prototype.hide = function(){
	goog.style.setStyle(this.promptDiv, "display", "none");
}

//退回商品添加确认
refund.OrderConfirmDialog = function(manager){
	this.refundManager = manager;
	this.confirmDialog = goog.dom.getElement('id-confirm-order-dialog');
	this.tid        = null;
	this.outer_id   = null;
	this.outer_sku_id  = null;
	this.order = null;

}

refund.OrderConfirmDialog.prototype.showdialog = function(order){
	this.order = order;
	var confirm_table = goog.dom.getElement('id-confirm-order-table');
	clearTable(confirm_table);
	addFirmOrderRow('id-confirm-order-table',order);
	
	var confirmOrderBtns = goog.dom.getElementsByClass('confirm-order');
	for(var i=0;i<confirmOrderBtns.length;i++){
		goog.events.listen(confirmOrderBtns[i], goog.events.EventType.CLICK,this.confirmRefundOrder,false,this);
	}
}

refund.OrderConfirmDialog.prototype.show = function(){
	var baseinfo_panel = goog.dom.getElement('id-baseinfo-table');
	var pos = goog.style.getPageOffset(baseinfo_panel);
	var scrollTop = document.body.scrollTop;
	goog.style.setPageOffset(this.confirmDialog,pos.x,scrollTop+77);
	goog.style.setStyle(this.confirmDialog, "display", "block");
}

refund.OrderConfirmDialog.prototype.hide = function(){
	goog.style.setStyle(this.confirmDialog, "display", "none");
}

refund.OrderConfirmDialog.prototype.confirmRefundOrder = function(e){
	var that   = this;
	var target = e.target;
	var idx    = target.getAttribute('idx');
	var confirm_num = goog.dom.getElement('id-confirm-num-'+idx).value;
	var reuse  = goog.dom.getElement('id-reuse-'+idx).checked;
	this.order['can_reuse'] = reuse;
	this.order['num']   = confirm_num;
	var refundTable = that.refundManager.refund_table;
	var callback = function(e){
		var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	if (res.code==0){
        		var order_dict = res.response_content;
        		addRefundOrderRow('id-refund-table',order_dict);
        		var curRowIndex = refundTable.rows.length;
        		if(curRowIndex>1){
        			goog.style.setStyle(refundTable.rows[curRowIndex-1],'background-color','green');
        			if (curRowIndex>2){
        				goog.style.setStyle(refundTable.rows[curRowIndex-2],'background-color','white');
        			}
        		}
        		that.refundManager.orderconfirm_dialog.hide();
        		showElement(refundTable.parentElement);
        		
        		var deleteOrderBtns = goog.dom.getElementsByClass('delete-order');
        		for(var i=0;i<deleteOrderBtns.length;i++){
        			goog.events.removeAll(deleteOrderBtns[i]);
            		goog.events.listen(deleteOrderBtns[i], goog.events.EventType.CLICK,that.refundManager.deleteOrder,false,that.refundManager);
        		}
        	}else{
        		alert("错误:"+res.response_error);
        	}
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	var content = goog.uri.utils.buildQueryDataFromMap(this.order);
	goog.net.XhrIo.send('/refunds/refund/',callback,'POST',content);
}

//主控制对象
goog.provide('refund.Manager');
/** @constructor */
refund.Manager = function () {

    this.prod_dicts  = null;

    this.prod_q   = goog.dom.getElement('id_prod_q');
    this.trade_q  = goog.dom.getElement('id_trade_q');
	this.search_trade_table = goog.dom.getElement('id-trade-search-table');
	this.search_prod_table  = goog.dom.getElement('id-prod-search-table');
	this.refund_table  = goog.dom.getElement('id-refund-table');
	this.clearBtn      = goog.dom.getElement('id_clear_btn');
	
	this.orderlist_dialog    = new refund.OrderListDialog(this);
    this.orderconfirm_dialog = new refund.OrderConfirmDialog(this);

	this.bindEvent();
}

//商品搜索事件处理
refund.Manager.prototype.onProdSearchKeyDown = function(e){
	
	var prod_qstr = this.prod_q.value;
	if (e.keyCode==13){
		this.showProduct(prod_qstr);	
	}
	this.hidePromptDialog();
	return;
}

//显示商品搜索记录
refund.Manager.prototype.showProduct = function (q) {
	this.search_q = q;
    var that      = this;
    if (q==''||q=='undifine'){return;};
    if (q.length>40){alert('搜索字符串不能超过40字');return;};

    var callback = function(e){
        var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	if (res.code == 0){
        		clearTable(that.search_prod_table);
        		
        		that.prod_dicts = res.response_content;
            	for(var i=0;i<that.prod_dicts.length;i++){
            		addSearchProdRow('id-prod-search-table',that.prod_dicts[i]);
            	}
            	
            	var addRefundOrderBtns = goog.dom.getElementsByClass('refund-order-add');
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

//添加退货商品
refund.Manager.prototype.addRefundOrder = function (e) {

	var target = e.target;
	var idx    = target.getAttribute('idx');
	var outer_id     = target.getAttribute('outer_id');
	var outer_sku_id = target.getAttribute('outer_sku_id');
	var tid    = target.getAttribute('tid');
	var title  = target.getAttribute('title');
	var property  = target.getAttribute('property');
	
	var cells  = target.parentElement.parentElement.cells;
	var buyer_nick = cells[0].innerHTML;

	if(idx!=null&&idx!='undifine'&&idx!=''){
		var sku_select = goog.dom.getElement('id-order-sku-'+idx);
		outer_sku_id = sku_select.value;
		buyer_nick   = goog.dom.getElement('id_buyer_nick').value;
		property = sku_select.options[sku_select.selectedIndex].innerHTML;
	}
	
	var memo      = goog.dom.getElement('id-return-memo').value;
	var buyer_mobile = goog.dom.getElement('id_receiver_mobile').value;
	var buyer_phone  = goog.dom.getElement('id_receiver_phone').value;
	var company   = goog.dom.getElement('id_return_company_name').value;
	var out_sid   = goog.dom.getElement('id_return_out_sid').value;

	var order_dict   = {
		'trade_id':tid,'outer_id':outer_id,'outer_sku_id':outer_sku_id,'title':title,'property':property,
		'memo':memo,'buyer_nick':buyer_nick,'buyer_mobile':buyer_mobile,
		'buyer_phone':buyer_phone,'out_sid':out_sid,'company':company
		};

	this.orderconfirm_dialog.showdialog(order_dict);
	this.orderconfirm_dialog.show();
}



//订单搜索事件处理
refund.Manager.prototype.onTradeSearchKeyDown = function(e){
	
	var prod_qstr = this.trade_q.value;
	if (e.keyCode==13){
		this.showTrade(prod_qstr);	
	}
	this.hidePromptDialog();
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
        try {
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
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	}
	goog.net.XhrIo.send('/trades/tradeplus/?q='+q,callback,'GET');
}

//显示交易订单列表信息
refund.Manager.prototype.showTradeOrderList = function(e){
	var that = this;
	var target = e.target;
	var trade_id = target.getAttribute('trade_id');
	this.orderlist_dialog.init(trade_id);
}

refund.Manager.prototype.hidePromptDialog = function(){
	this.orderlist_dialog.hide();
	this.orderconfirm_dialog.hide();
}

//删除退货商品
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
	new goog.ui.Zippy('id-refund-head', 'id-refund-goods');   
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
	this.hidePromptDialog();
}

