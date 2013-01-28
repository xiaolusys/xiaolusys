goog.require('goog.dom');
goog.require('goog.style');

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

var disableElement = function(el,status){
	goog.dom.setProperties(el,"disabled",status);
}

