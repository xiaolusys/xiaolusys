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
	this.dialog.setButtonSet(new goog.ui.Dialog.ButtonSet().addButton({key: 'CHECK', caption: "保存"},false,false));
	goog.events.listen(this.dialog, goog.ui.Dialog.EventType.SELECT, this);
    var tags = goog.dom.getElementsByClass("trade-tag");
    for(var i =0;i<tags.length;i++){
    	goog.events.listen(tags[i], goog.events.EventType.CLICK,this.showDialog,false,this);
    }
}

tradetag.Manager.prototype.showDialog = function(e) {
    var target   = e.target;
    this.tag_tid = target.getAttribute('trade_id');
    this.show(); 
}

tradetag.Manager.prototype.show = function(data) {
    this.dialog.setVisible(true);
}

tradetag.Manager.prototype.hide = function(data) {
    this.dialog.setVisible(false);
}

tradetag.Manager.prototype.handleEvent= function (e) {
	var action_code = '';
    if (e.key == 'CHECK') {
        action_code = 'check';
    }else if (e.key == 'REVIEW'){
        action_code = 'review';
    }
   
    return false;
}

tradetag.Manager.prototype.getDialogContent = function() {
    return '<div style="width:400px;"><div>'
  		+'<div class="memo_label"><label>买家昵称：</label><span id="id_buyer_nick"></span></div>'
  		+'<div class="memo_label"><label>收货人：</label><span id="id_receiver_name"></span></div>'
  		+'<div class="buyer_message_label"><label>买家留言：</label><p id="id_buyer_message"></p></div>'
  		+'</div><div><h3>卖家备注</h3>'
  		+'<div><textarea id="id_seller_memo" class="trade_memo"></textarea></div></div></div>'
}

