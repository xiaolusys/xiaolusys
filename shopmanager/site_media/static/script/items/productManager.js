goog.provide('product');
goog.provide('product.SkuDialog');
goog.provide('product.PromptDialog');

goog.require('goog.dom');
goog.require('goog.ui.Dialog');
goog.require('goog.ui.Zippy');
goog.require('goog.style');

goog.require('goog.net.XhrIo');
goog.require('goog.uri.utils');

/** @constructor
	修改库存对话框
 */
product.PromptDialog = function (manager) {
	this.inputText = null;
	this.manager   = manager;
    this.promptDiv = goog.dom.getElement('prompt-dialog');
    this.outer_id  = null;
    this.sku_id    = null; 
    this.promptBtn = goog.dom.getElement('prompt_submit');
    
    goog.events.listen(this.promptBtn, goog.events.EventType.CLICK, this.updateStock, false, this);
}

product.PromptDialog.prototype.init = function (elt ,outer_id,sku_id) {
	this.inputText = elt;
    this.outer_id = outer_id;
    this.sku_id   = sku_id; 
}


product.PromptDialog.prototype.show = function(data) {
	var pos = goog.style.getPageOffset(this.inputText);
    goog.style.setStyle(this.promptDiv,{'display':'block','position':'absolute'});
    goog.style.setPageOffset(this.promptDiv,pos);
    goog.dom.getElement('id_stock_num').focus();
}

product.PromptDialog.prototype.hide = function(data) {
    goog.style.setStyle(this.promptDiv,{'display':'none','position':'absolute'});
}

product.PromptDialog.prototype.updateStock = function(e) {
    var mode = null;
    var umodes = goog.dom.getElementsByTagNameAndClass('input','radio-mode');
    for(var i=0;i<umodes.length;i++){
    	console.log(umodes[i].checked);
    	if (umodes[i].checked){
    		mode=umodes[i].value;
    	}
    }
    var num = goog.dom.getElement('id_stock_num').value;
    if (mode==null||mode==''||mode=='undifine'||num==null||num=='undifine'||num==''){
    	alert('请输入库存数量！');
    	return false;
    }
    var params = {'mode':mode,'num':num,'outer_id':this.outer_id,'sku_id':this.sku_id};
    var that = this;
    var callback = function(e){
        var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	if(res.code==0){
        		var prod = res.response_content;
        		if (prod.sku){
        			that.inputText.value = prod.sku.quantity;
        			goog.dom.getElement('collect_num').value=prod.collect_num;
        		}else{
        			goog.dom.getElement('collect_num').value=prod.collect_num;
        		}
        		goog.dom.getElement('id_stock_num').value='';
        		that.hide();	
        	}
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/items/update/stock/',callback,'POST',content);
}

/** @constructor
	商品及规格信息管理对话框
 */
product.SkuDialog = function (manager) {
    this.dialog = new goog.ui.Dialog();
    this.productManager = manager;
    this.outer_id = null;
    
    this.promptdialog = new product.PromptDialog(this);
}

product.SkuDialog.prototype.init = function (id) {
	var dialog = this.dialog ;
    var that   = this ;
    this.outer_id = id;
    dialog.setContent('');
    var callback = function(e){
        var xhr = e.target;
        try {
        	var res = xhr.getResponse();
        	dialog.setContent(res);

    		dialog.setTitle('库存商品及规格信息管理对话框');
		    dialog.setButtonSet(new goog.ui.Dialog.ButtonSet());
			
			that.setEvent();
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	goog.net.XhrIo.send('/items/product/update/'+id+'/?format=html',callback,'GET');
}

product.SkuDialog.prototype.setEvent = function() {
	
	var dialogElement = this.dialog.getDialogElement();
	goog.events.listen(dialogElement,goog.events.EventType.CLICK,this.handleEvent,false,this);
    goog.events.listen(this.dialog, goog.ui.Dialog.EventType.AFTER_HIDE, this);
    
    var stockModifyInputs = goog.dom.getElementsByClass('stock-modify');
    for(var i=0;i<stockModifyInputs.length;i++){
    	goog.events.listen(stockModifyInputs[i], goog.events.EventType.FOCUS, this.showPrompt, false, this);
    }
}

product.SkuDialog.prototype.handleEvent = function(e){
	if (this.promptdialog){
		this.promptdialog.hide()
	}
}

product.SkuDialog.prototype.hidePrompt = function(e) {
    if (this.promptdialog){
		this.promptdialog.hide()
	}
}

product.SkuDialog.prototype.showPrompt = function(e) {
	var elt = e.target;
    var sku_id = elt.getAttribute('sku_id');
    this.promptdialog.init(elt,this.outer_id,sku_id);
    this.promptdialog.show()
}

product.SkuDialog.prototype.show = function(data) {
    this.dialog.setVisible(true);
    this.dialog.reposition();
}

product.SkuDialog.prototype.hide = function(data) {
    this.dialog.setVisible(false);
}


goog.provide("product.Manager");
product.Manager = function () {
    this.skudialog = new product.SkuDialog(this);
    this.buttons = goog.dom.getElementsByClass("product_modify");
    for(var i=0;i<this.buttons.length;i++){
        goog.events.listen(this.buttons[i], goog.events.EventType.CLICK, this.showDialog, false, this);
    }
}

product.Manager.prototype.showDialog = function(e) {
    var elt = e.target;
    var outer_id = elt.getAttribute('outer_id');
    if (outer_id==null||outer_id==''||outer_id=='undifine'){
    	outer_id = elt.parentElement.getAttribute('outer_id');
    }
    this.skudialog.init(outer_id);
    this.skudialog.show(); 

    return false;
}


product.Manager.prototype.handleEvent = function(e){
	return false;
}

