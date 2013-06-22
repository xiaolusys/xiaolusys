goog.provide('purchase');

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
    
	var id_cell       = createDTText(index+'');
	var img_cell      = goog.dom.createElement('td');
	img_cell.innerHTML = '<img width="80" height="80" src="'+prod[1]+'"></img>';
	
	var outer_id_cell = createDTText(prod[0]);
	var title_cell    = createDTText(prod[2]);
	
	var stock_cell    = createDTText(prod[4]);
	var price_cell    = createDTText(prod[3]);

	var addbtn_cell   = goog.dom.createElement('td');
	addbtn_cell.innerHTML = '<button class="show-prod-items btn btn-mini btn-info" style="margin:1px 0;" prod_id="'+prod.id+'">查看商品</button>';
	
	row.appendChild(id_cell);		
	row.appendChild(img_cell); 
	row.appendChild(outer_id_cell); 
	row.appendChild(title_cell);	 
	row.appendChild(stock_cell);		 
	row.appendChild(price_cell);	 
	row.appendChild(addbtn_cell);	 
}

//添加采购项目记录
var addPurchaseItemRow  = function(tableID,order){

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

//商品规格显示对话框
purchase.ProdItemListDialog = function(manager){
	this.Manager       = manager;
	this.promptDiv     = goog.dom.getElement('order-prompt');
	this.promptBody    = goog.dom.getElement('order-prompt-body');
	this.trade_id      = null;
	
	var closeBtn  = goog.dom.getElement('prompt-close');
	goog.events.listen(closeBtn, goog.events.EventType.CLICK,this.hide,false,this);
}

purchase.ProdItemListDialog.prototype.init = function(id){
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

purchase.ProdItemListDialog.prototype.show = function(){
	var trade_search_dialog = goog.dom.getElement('id-trade-search-dialog');
	var pos = goog.style.getPageOffset(trade_search_dialog);
	goog.style.setPageOffset(this.promptDiv,pos);
	goog.style.setStyle(this.promptDiv, "display", "block");
}

purchase.ProdItemListDialog.prototype.hide = function(){
	goog.style.setStyle(this.promptDiv, "display", "none");
}


//主控制对象
goog.provide('purchase.Manager');
/** @constructor */
purchase.Manager = function () {

    this.prod_dicts  = null;

    this.prod_q   = goog.dom.getElement('id_prod_q');
    this.trade_q  = goog.dom.getElement('id_trade_q');
	this.search_trade_table = goog.dom.getElement('id-trade-search-table');
	this.search_prod_table  = goog.dom.getElement('id-prod-search-table');
	this.refund_table  = goog.dom.getElement('id-refund-table');
	this.clearBtn      = goog.dom.getElement('id_clear_btn');
	this.clearListBtn  = goog.dom.getElement('id_clear_list_btn');
	
	this.orderlist_dialog    = new refund.OrderListDialog(this);
    this.orderconfirm_dialog = new refund.OrderConfirmDialog(this);

	this.bindEvent();
}

//商品搜索事件处理
purchase.Manager.prototype.onProdSearchKeyDown = function(e){
	
	var prod_qstr = this.prod_q.value;
	if (e.keyCode==13){
		this.showProduct(prod_qstr);	
	}
	this.hidePromptDialog();
	return;
}

//显示商品搜索记录
purchase.Manager.prototype.showProduct = function (q) {
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
purchase.Manager.prototype.addRefundOrder = function (e) {

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
		tid     =  goog.dom.getElement('id_trade_id').value;
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


//显示交易订单列表信息
purchase.Manager.prototype.showTradeOrderList = function(e){
	var that = this;
	var target = e.target;
	var trade_id = target.getAttribute('trade_id');
	this.orderlist_dialog.init(trade_id);
}

purchase.Manager.prototype.hidePromptDialog = function(){
	this.orderlist_dialog.hide();
	this.orderconfirm_dialog.hide();
}

//删除退货商品
purchase.Manager.prototype.deleteOrder = function(e){
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

//绑定事件
purchase.Manager.prototype.bindEvent = function () {

	goog.events.listen(this.prod_q, goog.events.EventType.KEYDOWN,this.onProdSearchKeyDown,false,this);
	
	goog.events.listen(this.prod_q, goog.events.EventType.FOCUS,this.focus,false,this);
	
	new goog.ui.Zippy('id-purchaseitem-head', 'id-return-goods');   
}

purchase.Manager.prototype.focus = function(e){

	showElement(this.search_prod_table.parentElement);

}

