goog.provide('ordercheck');
goog.provide('ordercheck.Dialog');

goog.require('goog.dom');
goog.require('goog.ui.Dialog');
goog.require('goog.style');

goog.require('goog.net.XhrIo');
goog.require('goog.uri.utils');


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
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	}
	goog.net.XhrIo.send('/trades/checkorder/'+id+'/?format=html',callback,'GET')
}

ordercheck.Dialog.prototype.show = function(data) {
    this.dialog.setVisible(true);
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
	goog.net.XhrIo.send('/trades/checkorder/'+trade_id+'/',callback,'POST',{'format':'json','logistic_code':logistic_code,'priority':priority});
}


new ordercheck.Manager()
