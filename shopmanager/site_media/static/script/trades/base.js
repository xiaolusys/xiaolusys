goog.require('goog.dom');
goog.require('goog.style');

var EXCHANGE_TRADE_TYPE = 'exchange'

var REAL_PAYMENT_TYPE = 0; 
var HANDSEL_TYPE      = 1;
var OVER_GIFT_TYPE    = 2;
var SPLIT_TYPE        = 3;
var RETURN_GOODS_TYPE = 4;
var CHANGE_GOODS_TYPE = 5;

var GIT_TYPE = {0:'实付',1:'赠送',2:'满就送',3:'拆分',4:'退货',5:'换货'}

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


