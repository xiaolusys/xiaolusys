goog.require('goog.dom');
goog.require('goog.style');

var EXCHANGE_TRADE_TYPE = 'exchange';
var DIRECT_TRADE_TYPE   = 'direct';

var REAL_PAYMENT_TYPE = 0; 
var HANDSEL_TYPE      = 1;
var OVER_GIFT_TYPE    = 2;
var SPLIT_TYPE        = 3;
var RETURN_GOODS_TYPE = 4;
var CHANGE_GOODS_TYPE = 5;

var GIT_TYPE = {0:'实付',1:'赠送',2:'满就送',3:'拆分',4:'退货',5:'换货'};
var REFUND_STATUS = {
	'WAIT_SELLER_AGREE':'买家申请退款，等待卖家同意',
	'WAIT_BUYER_RETURN_GOODS':'卖家已经同意退款，等待买家退货',
	'WAIT_SELLER_CONFIRM_GOODS':'买家已经退货，等待卖家确认收货',
	'SELLER_REFUSE_BUYER':'买家已经退货，等待卖家确认收货',
	'CLOSED':'退款关闭',
	'SUCCESS':'退款成功'};

var createDTText  = function(text){
    var td = goog.dom.createElement('td');
    td.appendChild(goog.dom.createTextNode(text));
    return td
}

var showElement   = function(el){
	goog.style.setStyle(el, "display", "block");
}

var hideElement   = function(el){
	goog.style.setStyle(el, "display", "none");
}

var clearTable    = function(table){
	for(var i=table.rows.length;i>1;i--){
		table.deleteRow(i-1);
	}
}


