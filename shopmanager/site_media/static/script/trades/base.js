goog.require('goog.dom');


var GIT_TYPE = {0:'实付',1:'赠送',2:'满就送',3:'拆分',4:'退货',5:'换货'}

var createDTText  = function(text){
    var td = goog.dom.createElement('td');
    td.appendChild(goog.dom.createTextNode(text));
    return td
}