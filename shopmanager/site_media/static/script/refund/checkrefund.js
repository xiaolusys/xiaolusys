goog.provide('checkrefund');
goog.provide('checkrefund.Dialog');
goog.provide('checkrefund.RelRefundDialog');

goog.require('goog.dom');
goog.require('goog.ui.Dialog');
goog.require('goog.ui.Zippy');
goog.require('goog.ui.TableSorter');
goog.require('goog.style');

goog.require('goog.net.XhrIo');
goog.require('goog.uri.utils');

/** @constructor 
	查看退货单详情对话框
*/
checkrefund.Dialog = function (manager) {
    this.dialog = new goog.ui.Dialog();
    this.refundManager = manager;
    this.refundTable   = null;
    this.tid = null;
    this.clickPos = null;
    this.refundTable   = goog.dom.getElement('id_refund_table'); 
}

checkrefund.Dialog.prototype.init = function (tid,seller_id) {
	var dialog = this.dialog ;
    var that   = this ;
    this.tid   = tid;
    this.seller_id = seller_id;
    dialog.setContent('');
    var params = {'tid':tid,'seller_id':this.seller_id,'format':'json'};
    
    var callback = function(e){
        var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	if (res.code==0){
	        	dialog.setContent(res.response_content.template_string);
	    		dialog.setTitle('退货单审核详情');
			    dialog.setButtonSet(new goog.ui.Dialog.ButtonSet().addButton({key: 'OK', caption: "确认收货并创建退换货单"},false,false));
			    goog.events.listen(dialog, goog.ui.Dialog.EventType.SELECT, that);
		    }else{
		    	that.hide();
		    	alert('错误:'+res.response_error);
		    }
	
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	}
	var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/refunds/manager/?',callback,'POST',content)
}

checkrefund.Dialog.prototype.show = function(data) {
    this.dialog.setVisible(true);
    var pos = this.clickPos;
    goog.style.setPageOffset(this.dialog.getDialogElement(),260,pos.y); 
}

checkrefund.Dialog.prototype.hide = function(data) {
    this.dialog.setVisible(false);
}

checkrefund.Dialog.prototype.handleEvent= function (e) {
	
    if (e.key == 'OK') {
		var url = '/refunds/exchange/'+this.seller_id+'/'+this.tid+'/';
		var row_idx = this.refundManager.check_row_idx;
		this.refundTable.deleteRow(row_idx);
		this.hide();
		window.open(url);  
    }
    return false;
}

/** @constructor 
	关联退货单对话框
*/
checkrefund.RelRefundDialog = function (manager) {
    this.promptDiv = goog.dom.getElement('rel-refundorder-dialog');
    this.refundText = goog.dom.getElement('relate_refund_tid');
    this.refundManager = manager;
    this.rpid     = null;
    this.clickPos = null;
    this.clickRowIndex = null;
    var confirmBtn = goog.dom.getElement('id_rel_refundbtn');
    goog.events.listen(confirmBtn, goog.events.EventType.CLICK, this.relatedRefund, false, this);
}


checkrefund.RelRefundDialog.prototype.show = function() {
	var pos = this.clickPos;
    goog.style.setStyle(this.promptDiv, "display", "block");
    goog.style.setPageOffset(this.promptDiv,pos.x-240,pos.y); 
    this.refundText.focus();
}

checkrefund.RelRefundDialog.prototype.hide = function() {
    goog.style.setStyle(this.promptDiv, "display", "none");
}

//确认退回商品关联退货单
checkrefund.RelRefundDialog.prototype.relatedRefund= function (e) {
	var elt = e.target;
	var that = this;
	var refund_tid = this.refundText.value;
	var params = {'refund_tid':refund_tid,'rpid':this.rpid};
	
	var callback = function(e){
        var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	if (res.code==0){
	        	that.hide();
	        	that.refundText.value='';
	        	var refundTable = goog.dom.getElement('id-refund-table');
	        	refundTable.deleteRow(that.clickRowIndex);
	        	that.clickRowIndex = null;
		    }else{
		    	alert('错误:'+res.response_error);
		    }
	
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	}
	var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/refunds/rel/?',callback,'POST',content)
}

goog.provide("checkrefund.Manager");
checkrefund.Manager = function () {
    this.dialog = new checkrefund.Dialog(this);
    this.relRefundDialog = new checkrefund.RelRefundDialog(this);
    this.check_row_idx = null;
    this.buttons = goog.dom.getElementsByClass("check-refund-order");
    for(var i=0;i<this.buttons.length;i++){
        goog.events.listen(this.buttons[i], goog.events.EventType.CLICK, this.showDialog, false, this);
    }
    
    var relRefundBtns = goog.dom.getElementsByClass("relate-refund");
    for(var i=0;i<relRefundBtns.length;i++){
        goog.events.listen(relRefundBtns[i], goog.events.EventType.CLICK, this.showRelRefundDialog, false, this);
    }
    
    var refundProdPanel = goog.dom.getElement('id-refund-head');
    goog.events.listen(refundProdPanel, goog.events.EventType.CLICK, this.hidePromptDialog, false, this); 
    
    var component = new goog.ui.TableSorter();
    var refund_table = goog.dom.getElement('id_refund_table');
    component.decorate(refund_table);
    component.setSortFunction(1, goog.ui.TableSorter.alphaSort);
    component.setSortFunction(2,
        goog.ui.TableSorter.createReverseSort(goog.ui.TableSorter.numericSort));
        
    new goog.ui.Zippy('id-refund-head', 'id-refund-goods'); 
}

checkrefund.Manager.prototype.showDialog = function(e) {
    var elt = e.target;
    var trade_id = elt.getAttribute('tid');
    var seller_id = elt.getAttribute('seller_id');
    this.dialog.init(trade_id,seller_id);
    this.dialog.clickPos = goog.style.getPageOffset(elt);
    this.check_row_idx = elt.parentElement.parentElement.rowIndex;
    this.dialog.show(); 
}

checkrefund.Manager.prototype.showRelRefundDialog = function(e) {
    var elt = e.target;
    var rpid = elt.getAttribute('rpid');
	this.relRefundDialog.rpid = rpid;
	this.relRefundDialog.clickRowIndex = elt.parentElement.parentElement.rowIndex;
	this.relRefundDialog.clickPos = goog.style.getPageOffset(elt);
	this.relRefundDialog.show();
}

checkrefund.Manager.prototype.hidePromptDialog = function(e) {
     this.relRefundDialog.hide();
}
