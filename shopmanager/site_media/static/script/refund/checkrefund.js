goog.provide('checkrefund');
goog.provide('checkrefund.Dialog');

goog.require('goog.dom');
goog.require('goog.ui.Dialog');
goog.require('goog.ui.Zippy');
goog.require('goog.ui.TableSorter');
goog.require('goog.style');

goog.require('goog.net.XhrIo');
goog.require('goog.uri.utils');

/** @constructor */
checkrefund.Dialog = function (manager) {
    this.dialog = new goog.ui.Dialog();
    this.refundManager = manager;
    this.refundTable   = null;
    this.tid = null;
    
    this.refundTable   = goog.dom.getElement('id_refund_table'); 
}

checkrefund.Dialog.prototype.init = function (tid) {
	var dialog = this.dialog ;
    var that   = this ;
    this.tid   = tid;
    dialog.setContent('');
    var params = {'tid':tid,'format':'json'};
    
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
}

checkrefund.Dialog.prototype.hide = function(data) {
    this.dialog.setVisible(false);
}

checkrefund.Dialog.prototype.handleEvent= function (e) {
    if (e.key == 'OK') {
		var url = '/refunds/exchange/'+this.tid+'/';
		var row_idx = this.refundManager.check_row_idx;
		this.refundTable.deleteRow(row_idx);
		this.hide();
		window.open(url);  
    }
    return false;
}

goog.provide("checkrefund.Manager");
checkrefund.Manager = function () {
    this.dialog = new checkrefund.Dialog(this);
    this.check_row_idx = null;
    this.buttons = goog.dom.getElementsByClass("check-refund-order");
    for(var i=0;i<this.buttons.length;i++){
        goog.events.listen(this.buttons[i], goog.events.EventType.CLICK, this.showDialog, false, this);
    }
    
    var component = new goog.ui.TableSorter();
    var refund_table = goog.dom.getElement('id_refund_table');
    console.log(refund_table);
    component.decorate(refund_table);
    component.setSortFunction(1, goog.ui.TableSorter.alphaSort);
    component.setSortFunction(2,
        goog.ui.TableSorter.createReverseSort(goog.ui.TableSorter.numericSort));
}

checkrefund.Manager.prototype.showDialog = function(e) {
    var elt = e.target;
    var trade_id = elt.getAttribute('tid');
    this.dialog.init(trade_id);
    this.check_row_idx = elt.parentElement.parentElement.rowIndex;
    this.dialog.show(); 
}
