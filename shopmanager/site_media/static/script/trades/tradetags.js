goog.provide('tradetag');
goog.provide('tradetag.Dialog');

goog.require('goog.dom');
goog.require('goog.ui.Dialog');

goog.require('goog.net.XhrIo');
goog.require('goog.uri.utils');


goog.provide("tradetag.Manager");
tradetag.Manager = function () {
    this.dialog  = new goog.ui.Dialog();
    this.tag_tid = null;
    this.dialog.setContent(this.getDialogContent());
    
    this.dialog.setTitle('订单留言');
	this.dialog.setButtonSet(new goog.ui.Dialog.ButtonSet().addButton({key: 'SAVE', caption: "保存"},false,false));
	goog.events.listen(this.dialog, goog.ui.Dialog.EventType.SELECT, this);
    var tags = goog.dom.getElementsByClass("trade-tag");
    for(var i =0;i<tags.length;i++){
    	goog.events.listen(tags[i], goog.events.EventType.CLICK,this.showDialog,false,this);
    }
}

tradetag.Manager.prototype.showDialog = function(e) {
	var that     = this;
    var target   = e.target.parentElement;
    this.tag_tid = target.getAttribute('trade_id');
    this.show();
    var callback = function(e){
    	var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	if (res.id!=''||res.id!='undifine'){
        		goog.dom.getElement('id_buyer_nick').innerHTML    = res.buyer_nick;
        		goog.dom.getElement('id_receiver_name').innerHTML = res.receiver_name;
        		goog.dom.getElement('id_buyer_message').innerHTML = res.buyer_message;
        		goog.dom.getElement('id_seller_message').innerHTML= res.seller_memo;
        		goog.dom.getElement('id_sys_memo').value          = res.sys_memo;		
        	}else{
        		alert('订单获取失败！');
        	}
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
    };
	goog.net.XhrIo.send('/trades/trade/'+this.tag_tid+'/?format=json',callback,'GET'); 
}

tradetag.Manager.prototype.show = function(data) {
    this.dialog.setVisible(true);
}

tradetag.Manager.prototype.hide = function(data) {
    this.dialog.setVisible(false);
}

tradetag.Manager.prototype.handleEvent= function (e) {
	var that = this;
    if (e.key == 'SAVE') {
        var sys_memo = goog.dom.getElement('id_sys_memo').value;
        var callback = function(e){
	    	var xhr = e.target;
	        try {
	        	var res = xhr.getResponseJson();
	        	if (res.code == 0){
					that.hide();
	        	}else{
	        		alert('订单备注失败！');
	        	}
	        } catch (err) {
	            console.log('Error: (ajax callback) - ', err);
	        } 
	    };
	    var params  = {'sys_memo':sys_memo,'trade_id':this.tag_tid};
		var content = goog.uri.utils.buildQueryDataFromMap(params);
	    goog.net.XhrIo.send('/trades/memo/',callback,'POST',content); 
    }
    return false;
}

tradetag.Manager.prototype.getDialogContent = function() {
    return '<div style="width:400px;"><div>'
  		+'<div class="memo_label"><label>买家昵称：</label><span id="id_buyer_nick"></span></div>'
  		+'<div class="memo_label"><label>收货人：</label><span id="id_receiver_name"></span></div>'
  		+'<div class="buyer_message_label"><label>买家留言：</label><span id="id_buyer_message"></span></div>'
  		+'<div class="seller_message_label"><label>卖家留言：</label><span id="id_seller_message"></span></div>'
  		+'</div><div><h3>系统备注</h3>'
  		+'<div><textarea id="id_sys_memo" class="trade_memo"></textarea></div></div></div>'
}

