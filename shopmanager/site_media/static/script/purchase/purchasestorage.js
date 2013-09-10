goog.provide('purchasestorage');

goog.require('goog.dom');
goog.require('goog.ui.Dialog');
goog.require('goog.ui.Zippy');
goog.require('goog.style');
goog.require('goog.ui.Component.EventType');

goog.require('goog.net.XhrIo');
goog.require('goog.uri.utils');


/**修改一条datatable记录*/
function editRow ( oTable, nRow )
{
	var aData = oTable.fnGetData(nRow);
	var jqTds = $('>td', nRow);
	jqTds[5].innerHTML = '<input type="text" class="edit-price" value="'+aData[5]+'">';
	jqTds[6].innerHTML = '<a class="save" href="#"><icon class="icon-ok"></icon></a>'
		+'<a class="delete" href="#"><icon class="icon-remove"></icon></a>';
}

/**保存一条datatable记录*/
function saveRow ( oTable, nRow )
{
	var jqInputs = $('input', nRow);
	oTable.fnUpdate( jqInputs[0].value, nRow, 5, false );
	oTable.fnUpdate( '<a class="edit" href="#"><icon class="icon-pencil"></a>'+
		'<a class="delete" href="#"><icon class="icon-remove"></icon></a>', nRow, 6, false );
	oTable.fnDraw();
}

//添加商品搜索结果
var addSearchProdRow  = function(tableID,prod){

	var table    = goog.dom.getElement(tableID);
	var rowCount = table.rows.length;
    var row      = table.insertRow(rowCount);
    var index    = rowCount;
    
	var id_cell        = createDTText(index+'');
	var img_cell       = goog.dom.createElement('td');
	img_cell.innerHTML = '<img width="40" height="60" margin="0" src="'+prod[1]+'"></img>';
	
	var outer_id_cell = createDTText(prod[0]);
	var title_cell    = createDTText(prod[2]);
	
	var stock_cell    = createDTText(prod[4]);
	var created_cell    = createDTText(prod[5]);
	
	var addbtn_cell   = goog.dom.createElement('td');
	addbtn_cell.innerHTML = '<button class="select-purchase-items btn btn-mini btn-info" style="margin:1px 0;" prod_id="'+prod[0]+'">查看规格</button>';
	
	row.appendChild(id_cell);		
	row.appendChild(img_cell); 		
	row.appendChild(outer_id_cell); 
	row.appendChild(title_cell);	 
	row.appendChild(stock_cell);		 
	row.appendChild(created_cell);	 
	row.appendChild(addbtn_cell);	 
}

//添加商品规格条目
var addPurchaseItemRow  = function(tableID,prod,sku){

	var table = goog.dom.getElement(tableID);
	var rowCount = table.rows.length;
    var row   = table.insertRow(rowCount);
    var index = rowCount;
    
	var id_cell       = createDTText(index+'');
	
	var outer_id_cell = createDTText(prod[0]);
	var title_cell    = createDTText(prod[2]);
	
	var sku_id_cell   = createDTText(sku[0]);
	var sku_name_cell = createDTText(sku[1]);
	
	
	var num_cell       = goog.dom.createElement('td');
	num_cell.innerHTML = '<input type="text" class="edit-num" value="0" />';
	
	var addbtn_cell   = goog.dom.createElement('td');
	addbtn_cell.innerHTML = '<button class="add-purchase-item btn btn-mini btn-info" style="margin:1px 0;" >添加</button>';
	
	row.appendChild(id_cell);		
	row.appendChild(outer_id_cell); 
	row.appendChild(title_cell);
	row.appendChild(sku_id_cell); 	 
	row.appendChild(sku_name_cell);		 
	row.appendChild(num_cell);	 
	row.appendChild(addbtn_cell);	 
}


//采购项目选择对话框
purchasestorage.PurchaseSelectDialog = function(manager){
	this.manager       = manager;
	this.promptDiv     = goog.dom.getElement('purchase-prompt');
	this.promptBody    = goog.dom.getElement('purchase-prompt-body');
	this.purchase_select_table = goog.dom.getElement('purchase-select-table'); 
	this.prod      = null;
	
	var closeBtn  = goog.dom.getElement('prompt-close');
	goog.events.listen(closeBtn, goog.events.EventType.CLICK,this.hide,false,this);
}


purchasestorage.PurchaseSelectDialog.prototype.init = function(prod){
	
	this.prod = prod;
	var prod_sku  = prod[6];
	clearTable(this.purchase_select_table);
	
	for(var i=0;i<prod_sku.length;i++){
		addPurchaseItemRow('purchase-select-table',prod,prod_sku[i]);
	}
	
	var add_pch_item_btns =  goog.dom.getElementsByClass('add-purchase-item');
	for(var i=0;i<add_pch_item_btns.length;i++){
		goog.events.listen(add_pch_item_btns[i], goog.events.EventType.CLICK,this.manager.onCreatePurchaseItem,false,this.manager);
	}
}


purchasestorage.PurchaseSelectDialog.prototype.show = function(){
	var scrollHeight = $(document).scrollTop();
	var pos = goog.style.getPageOffset(this.manager.search_prod_table);
	goog.style.setPageOffset(this.promptDiv,pos.x,scrollHeight+pos.y);
	goog.style.setStyle(this.promptDiv, "display", "block");
}


purchasestorage.PurchaseSelectDialog.prototype.hide = function(){
	goog.style.setStyle(this.promptDiv, "display", "none");
}


//主控制对象
goog.provide('purchasestorage.Manager');
/** @constructor */
purchasestorage.Manager = function () {

    this.proditems     = {};
    this.purchasestorageid_label = goog.dom.getElement('id_purchase_storage');
    this.prod_q        = goog.dom.getElement('id_prod_q');
	this.search_prod_table  = goog.dom.getElement('id-prod-search-table');
	this.saveBtn       = goog.dom.getElement('save_purchase');
	this.checkBtn      = goog.dom.getElement('check_purchase');
	
	this.prompt_dialog = new purchasestorage.PurchaseSelectDialog(this);
	this.datatable     = null;
	this.nEditing      = null;//datatable当前选定行
	this.bindEvent();
}


//商品搜索事件处理
purchasestorage.Manager.prototype.onProdSearchKeyDown = function(e){
	
	var prod_qstr = this.prod_q.value;
	var purchase_storage_id = this.purchasestorageid_label.innerHTML;
	if (e.keyCode==13){
		if (purchase_storage_id==null||purchase_storage_id==''||purchase_storage_id=='undifine'){
			alert('请先保存采购单基本信息');
			return;
		}
		this.showProduct(prod_qstr);	
	}
	return;
}


//添加采购项
purchasestorage.Manager.prototype.onCreatePurchaseItem = function(e){
	var target    = e.target;
	var row       = target.parentElement.parentElement;
	
	$('#purchase-items').show();
	var params = {  'purchase_storage_id':this.purchasestorageid_label.innerHTML,
					'outer_id':row.cells[1].innerHTML,
					'sku_id':row.cells[3].innerHTML,
					'num':row.cells[5].firstChild.value};
	var that = this;
	var callback = function(e){
		var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	if (res.code==0){
        		var purchase_item = res.response_content;
        		that.datatable.fnAddData( [ purchase_item.id,
									purchase_item.outer_id, 
									purchase_item.name, 
									purchase_item.outer_sku_id, 
									purchase_item.properties_name,
									purchase_item.storage_num, 
									'<a class="edit" href="#"><icon class="icon-pencil"></icon></a>'+
									'<a class="delete" href="#"><icon class="icon-remove"></icon></a>']);
				goog.style.setStyle(row,'background-color','#BFCEEC');
				goog.style.showElement(row.cells[6].firstChild, false);
				that.calPurchaseNumAndFee();
        	}else{
        		alert("错误:"+res.response_error);
        	}
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        }
	};
	var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/purchases/storage/item/',callback,'POST',content);
}

//添加采购项
purchasestorage.Manager.prototype.savePurchaseItem = function(nRow){
	
	var params = {  'purchase_storage_id':this.purchasestorageid_label.innerHTML,
					'outer_id':nRow.cells[1].innerHTML,
					'sku_id':nRow.cells[3].innerHTML,
					'num':nRow.cells[5].firstChild.value};
	var that = this;
	var callback = function(e){
		var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	if (res.code==0){
        		var purchase_item = res.response_content;
        		var jqInputs = $('input', nRow);
				that.datatable.fnUpdate( jqInputs[0].value, nRow, 5, false );
				that.datatable.fnUpdate( '<a class="edit" href="#"><icon class="icon-pencil"></a>'+
					'<a class="delete" href="#"><icon class="icon-remove"></icon></a>', nRow, 6, false );
				that.datatable.fnDraw();
        	}else{
        		alert("错误:"+res.response_error);
        	}
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/purchases/storage/item/',callback,'POST',content);
}

//删除采购项
purchasestorage.Manager.prototype.delPurchaseItem = function(nRow){
	
	var purchase_item_id = nRow.cells[0].innerHTML;
	if(!confirm("确定删除入库项目 "+purchase_item_id+" 吗？"))
	{
	    return;
	}
	var params = {  'purchase_storage_id':this.purchasestorageid_label.innerHTML,
					'purchase_storage_item_id':purchase_item_id};
	var that = this;
	var callback = function(e){
		var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	if (res.code==0){
      			that.datatable.fnDeleteRow( nRow );
        	}else{
        		alert("错误:"+res.response_error);
        	}
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/purchases/storage/item/del/',callback,'POST',content);
}

//添加采购基本信息
purchasestorage.Manager.prototype.onSavePurchaseInfo = function(e){
	
	var that = this;
	var supplier = $('#supplier').val();
	if (supplier==''||supplier=='undifine'){
		alert('请输入供应商');
		return;
	}
	var params = {  'origin_no':$('#origin_no').val(),
					'purchase_storage_id':this.purchasestorageid_label.innerHTML,
					'supplier_id':supplier,
					'deposite_id':$('#deposite').val(),
					'forecast_date':$('#forecast_date').val(),
					'post_date':$('#post_date').val(),
					'extra_name':$('#extra_name').val(),
					'extra_info':$('#extra_info').val()
			};
					
	var callback = function(e){
		var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	if (res.code==0){
        		var purchasestorageins = res.response_content;
        		var purchase_storage_id = that.purchasestorageid_label.innerHTML;
     			if (purchase_storage_id==''||purchase_storage_id=='undifine'){
     				window.location='/purchases/storage/'+purchasestorageins.id+'/';
     			}else{
     				alert('保存成功！');
     			}
        	}else{
        		alert("错误:"+res.response_error);
        	}
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	var content = goog.uri.utils.buildQueryDataFromMap(params);
	goog.net.XhrIo.send('/purchases/storage/add/?format=json',callback,'POST',content);
}

//审核采购合同
purchasestorage.Manager.prototype.onCheckPurchaseInfo = function(e){
	
	var purchase_storage_id = this.purchasestorageid_label.innerHTML;
	
	if (purchase_storage_id==''||purchase_storage_id=='undifine'){
		alert('请先保存采购基本信息');
		return;
	}
	window.location = "/admin/purchases/purchasestorage/?status__exact=DRAFT&q="+purchase_storage_id;
}

//显示商品搜索记录
purchasestorage.Manager.prototype.showProduct = function (q) {
	this.search_q = q;
    var that      = this;
    if (q==''||q=='undifine'){return;};
    if (q.length>40){alert('搜索字符串不能超过40字');return;};

    var callback = function(e){
        var xhr = e.target;
        try {
        	var res = xhr.getResponseJson();
        	if (res.code == 0){
        		clearTable(that.search_prod_table);
        
        		var prod_list = res.response_content;
            	for(var i=0;i<prod_list.length;i++){
            		that.proditems[prod_list[i][0]] = prod_list[i]
            		addSearchProdRow('id-prod-search-table',prod_list[i]);
            	}

            	var slt_ph_btns = goog.dom.getElementsByClass('select-purchase-items');
            	for(var i=0;i<slt_ph_btns.length;i++){
            		goog.events.listen(slt_ph_btns[i], goog.events.EventType.CLICK,that.onShowPurchaseItems,false,that);
            	}
            }else{
                alert("商品查询失败:"+res.response_error);
            }
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	}
	goog.net.XhrIo.send('/items/query/?q='+q,callback);
}


//响应点击查看采购项事件
purchasestorage.Manager.prototype.onShowPurchaseItems = function (e) {
	
	var target    = e.target;
	var prod_id   = target.getAttribute('prod_id');
	var prod      = this.proditems[prod_id];

	this.prompt_dialog.init(prod);
	this.prompt_dialog.show();
}


//添加退货商品
purchasestorage.Manager.prototype.addRefundOrder = function (e) {

	var target = e.target;
	var idx    = target.getAttribute('idx');
	var outer_id     = target.getAttribute('outer_id');
	var outer_sku_id = target.getAttribute('outer_sku_id');
	
}


//显示交易订单列表信息
purchasestorage.Manager.prototype.hidePromptDialog = function(){
	this.orderlist_dialog.hide();
	this.orderconfirm_dialog.hide();
}


//计算采购单数量及费用
purchasestorage.Manager.prototype.calPurchaseNumAndFee = function(){
	var total_num = 0;
	var cell_num  = 0;
 	var row = null;

	var rows = $("#purchaseitem-table > tbody > tr");
	for(var i=0;i < rows.length;i++){
		row = rows[i];
		if (row.cells.length < 7){continue;}
		
		cell_num = row.cells[5].innerHTML;
	
		if(parseInt(cell_num)){
			total_num += parseInt(cell_num);
		}else{
			cell_num = $('input',row.cells[5]).val();
			if (parseInt(cell_num)){
				total_num += parseInt(cell_num);
			}
		}
	}
	$('#total_num').val(total_num.toString());
}


//绑定事件
purchasestorage.Manager.prototype.bindEvent = function (){

	goog.events.listen(this.prod_q, goog.events.EventType.KEYDOWN,this.onProdSearchKeyDown,false,this);
	
	goog.events.listen(this.saveBtn, goog.events.EventType.CLICK,this.onSavePurchaseInfo,false,this);
	   
	$("#purchase-prompt").draggable({handle: $('#purchase-prompt-head')});
	
	/**对jquery的datatable表格进行初始化*/
	this.datatable = $('#purchaseitem-table').dataTable({
   		//"bJQueryUI": true,
		"bAutoWidth": false, //自适应宽度
		"aaSorting": [[1, "asc"]],
		"iDisplayLength": 20,
		"aLengthMenu": [[20, 50, 100, -1], [20, 50, 100, "All"]],
		//"sPaginationType": "full_numbers",
		//"sDom": '<"H"Tfr>t<"F"ip>',
		"oLanguage": {
			"sLengthMenu": "每页 _MENU_ 条",
			"sZeroRecords": "抱歉， 没有找到",
			"sInfo": "从 _START_ 到 _END_ /共 _TOTAL_ 条",
			"sInfoEmpty": "没有数据",
			"sSearch": "搜索",
			"sInfoFiltered": "(从 _MAX_ 条数据中检索)",
			"oPaginate": {
				"sFirst": "首页",
				"sPrevious": "前一页",
				"sNext": "后一页",
				"sLast": "尾页"
			},
			"sZeroRecords": "没有检索到数据",
			"sProcessing": "<img src='/static/img/loading.gif' />"
		}		
	});

	//数量，费用初始化
	this.calPurchaseNumAndFee();
	
	var that = this;
	//设置每页显示数量时，重新计算
	$("select[name='purchaseitem-table_length']").change(function(e){
		e.preventDefault();
		that.calPurchaseNumAndFee();
	});
	
	//搜索时，重新计算
	$("#purchaseitem-table_filter input").keyup(function(e){
		e.preventDefault();
		that.calPurchaseNumAndFee();
	});
	
	//分页时，重新计算
	$("#purchaseitem-table_paginate a").click(function(e){
		e.preventDefault();
		that.calPurchaseNumAndFee();
	});
	
	//绑定删除事件
	$('#purchaseitem-table a.delete').live('click', function (e) {
		e.preventDefault();
		
		var nRow = $(this).parents('tr')[0];
		that.delPurchaseItem(nRow);
		that.calPurchaseNumAndFee();
	} );
	//绑定保存事件
	$('#purchaseitem-table a.save').live('click', function (e) {
		e.preventDefault();
		
		var nRow = $(this).parents('tr')[0];
		that.savePurchaseItem(nRow);
		that.nEditing = null;
		that.calPurchaseNumAndFee();
	} );
	//绑定编辑事件
	$('#purchaseitem-table a.edit').live('click', function (e) {
		e.preventDefault();
		/* Get the row as a parent of the link that was clicked on */
		var nRow = $(this).parents('tr')[0];

		if ( that.nEditing !== null && that.nEditing != nRow ) {
			/* Currently editing - but not this row - restore the old before continuing to edit mode */
			restoreRow( that.datatable, that.nEditing );
			editRow( that.datatable, nRow );
			that.nEditing = nRow;
		}else {
			/* No edit in progress - let's start one */
			editRow( that.datatable, nRow );
			that.nEditing = nRow;
		}
	});

	//绑定数量修改按键事件
	$('input.edit-num').live('keyup', function (e) {
		
		e.preventDefault();
		var target = e.target;
		
		var num = target.value;
		
		if (parseInt(num)){
			target.value = parseInt(num).toString();
		}else{
			target.value = '0';
		}
	} );
	//选择日期

	$("#forecast_date").datepicker({ dateFormat: "yy-mm-dd" });
	$("#post_date").datepicker({ dateFormat: "yy-mm-dd" });
}




