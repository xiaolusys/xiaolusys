goog.provide('purchasepayment');

goog.require('goog.dom');
goog.require('goog.ui.Dialog');
goog.require('goog.ui.Zippy');
goog.require('goog.style');
goog.require('goog.ui.Component.EventType');

goog.require('goog.net.XhrIo');
goog.require('goog.uri.utils');



var CONFIRM_DIALOG_TEMPLATE = 
	'<form class="form-horizontal" action="/purchases/payment/confirm/" method="POST">'
	+'<div style="display:none;">'
	+'<input type="text" id="id" name="id" value="" />'
	+'</div><div class="control-group">'
	+'<label class="control-label" for="pay_bank">付款银行（平台）</label>'
	+'<div class="controls">'
	+'<input type="text" name="pay_bank" />'
	+'</div></div>'
	+'<div class="control-group">'
	+'<label class="control-label" for="pay_no">银行支付流水号</label>'
	+'<div class="controls">'
	+'<input type="text" name="pay_no" />'
	+'</div></div>'
	+'<div class="control-group">'
	+'<label class="control-label" for="pay_time">付款日期</label>'
	+'<div class="controls">'
	+'<input id="pay_time" type="text" name="pay_time" />'
	+'</div></div>'
	+'<div class="control-group">'
	+'<div class="controls">'
	+'<input type="submit" class="btn btn-primary" value="提交">'
	+'</div></div>'
	+'</form>';

goog.provide('purchasepayment.ConfirmDialog');
purchasepayment.ConfirmDialog = function(manager){
	this.manager   =  manager;
	this.dialog    =  new goog.ui.Dialog();
	
	this.dialog.setContent(CONFIRM_DIALOG_TEMPLATE);
	this.dialog.setTitle('采购付款单确认对话框');
	this.dialog.setButtonSet(new goog.ui.Dialog.ButtonSet());
	
} 

purchasepayment.ConfirmDialog.prototype.show = function(){
	this.dialog.setVisible(true);
	$("#pay_time").datepicker({ dateFormat: "yy-mm-dd" });
	var purchase_payment_id = $('#purchase_payment_id').val();
	$('#id').val(purchase_payment_id);
}

purchasepayment.ConfirmDialog.prototype.hide = function(){
	this.dialog.setVisible(false);
}


//主控制对象
goog.provide('purchasepayment.Manager');
/** @constructor */
purchasepayment.Manager = function () {
	
	this.confirmBtn     = goog.dom.getElement('confirm-payment');
	this.confirmdialog  = new purchasepayment.ConfirmDialog(this);
	
	goog.events.listen(this.confirmBtn, goog.events.EventType.CLICK,
		this.confirmdialog.show,false,this.confirmdialog); 
		
	$('input[id^="purchase-"]').keypress(function(event) {
		if ( event.which == 13 ) {
	  
	     event.preventDefault();
	     var target = event.target;
	     var payment   = parseFloat(target.value);
	     
         if (payment<=0){
     	    payment.value = '0';	
     	    return
     	 }
	     if (target.id.match(/^purchase-[0-9]+$/)){
	     
	     	var unpay_fee = parseFloat($(target).attr('unpay_fee'));
	     	var regex_id = target.id+'-';
	     	var items = $('input[id^="'+regex_id+'"]');
	     	
	     	for (var i=0;i<items.length;i++){
	     		items[i].value = ((parseFloat($(items[i]).attr('unpay_fee'))/unpay_fee)*payment).toFixed(2).toString();
	     	}
	     }else{
	     	payment = 0;
	     	var pid = target.id.slice(0,target.id.lastIndexOf('-'));
	     	var items = $('input[id^="'+pid+'-"]');
	     	
	     	for (var i=0;i<items.length;i++){
	     		payment += parseFloat(items[i].value);
	     		items[i].value = parseFloat(items[i].value).toFixed(2).toString();
	     	}
	     	$('#'+pid).val(payment.toFixed(2).toString());
	     }
	   } 
	 }
	);
}


