/**全局变量*/
var dtable      = null; //datatable对象
var nEditing    = null; //当前编辑行
var MONEY_FIXED = 4;    //成本计算精度
var product_id  = null; //商品编码

/**恢复一条datatable记录，*/
function restoreRow ( oTable, nRow )
{
	var aData = oTable.fnGetData(nRow);
	var jqTds = $('>td', nRow);
	
	for ( var i=0, iLen=jqTds.length ; i<iLen ; i++ ) {
		oTable.fnUpdate( aData[i], nRow, i, false );
	}
	oTable.fnDraw();
}

//计算商品库存及总成本
function calProductNumAndCost(){
	var total_num = 0;
	var total_fee = 0.0;
	var cell_num  = 0;
	var cell_fee  = 0.0;
 	var row = null;
 	var fee_cell  = null;
 	
	var rows = $("#productsku-table > tbody > tr");
	for(var i=0;i < rows.length;i++){
		row = rows[i];
		if (row.cells.length < 13){continue;}
		
		fee_cell = $('input',row.cells[8]);
		
		cell_num = parseInt($('input',row.cells[4]).val());

		total_num += cell_num;
		if(fee_cell.length>0){
			cell_fee = parseFloat(fee_cell.val());
		}else{
			cell_fee = parseFloat(row.cells[8].innerHTML);
		}
		
		total_fee += cell_num*cell_fee;
	}
	$('#total_num').val(total_num.toString());
	$('#total_cost').val(total_fee.toFixed(MONEY_FIXED).toString())
}

/**修改一条datatable记录*/
function editRow ( oTable, nRow )
{
	var aData = oTable.fnGetData(nRow);
	var jqTds = $('>td', nRow);
	jqTds[1].innerHTML = '<input type="text" value="'+aData[1]+'">';
	jqTds[3].innerHTML = '<input type="text" style="width:130px;" value="'+aData[3]+'">';
	jqTds[5].innerHTML = '<input type="text" value="'+aData[5]+'">';
	jqTds[6].innerHTML = '<input type="text" value="'+aData[6]+'">';
	jqTds[7].innerHTML = '<input type="text" value="'+aData[7]+'">';
	jqTds[8].innerHTML = '<input type="text" value="'+aData[8]+'" >';
	jqTds[9].innerHTML = '<input type="text" value="'+aData[9]+'" >';
	jqTds[10].innerHTML = '<input type="text" value="'+aData[10]+'" >';
	jqTds[11].innerHTML = '<input type="text" value="'+aData[11]+'" >';
	jqTds[12].innerHTML = '<a class="save"  href="#" title="保存"><icon class="icon-ok"></icon></a>'+
						'<a class="setup" href="#" title="设置"><icon class="icon-asterisk"></icon></icon></a>'+
						'<a class="remain" href="#" title="待用"><icon class="icon-pause"></icon></icon></a>'+
						'<a class="delete" href="#" title="作废"><icon class="icon-remove"></icon></icon></a>';
}


/**保存一条datatable记录*/
function saveRow ( oTable, nRow )
{
	var jqInputs = $('input', nRow);
	oTable.fnUpdate( jqInputs[0].value, nRow, 1, false );
	oTable.fnUpdate( jqInputs[1].value, nRow, 3, false );
	oTable.fnUpdate( jqInputs[2].value, nRow, 5, false );
	oTable.fnUpdate( jqInputs[3].value, nRow, 6, false );
	oTable.fnUpdate( jqInputs[4].value, nRow, 7, false );
	oTable.fnUpdate( jqInputs[5].value, nRow, 8, false );
	oTable.fnUpdate( jqInputs[6].value, nRow, 9, false );
	oTable.fnUpdate( jqInputs[7].value, nRow, 10, false );
	oTable.fnUpdate( jqInputs[8].value, nRow, 11, false );
	oTable.fnUpdate( '<a class="edit"   href="#" title="修改"><icon class="icon-edit"></icon></a>'+
					'<a class="setup" href="#" title="设置"><icon class="icon-asterisk"></icon></icon></a>'+
					'<a class="remain" href="#" title="待用"><icon class="icon-pause"></icon></icon></a>'+
					'<a class="delete" href="#" title="作废"><icon class="icon-remove"></icon></icon></a>', nRow, 12, false );
	oTable.fnDraw();
}

/** 保存修改商品信息 */
function saveProductAction(nRow)
{	
	var sku_id = $(nRow.cells[0]).contents().get(0).nodeValue;
	var params = {
		'outer_id':nRow.cells[1].firstChild.value,
		'properties_alias':nRow.cells[3].firstChild.value,
		'wait_post_num':nRow.cells[5].firstChild.value,
		'remain_num':nRow.cells[6].firstChild.value,
		'warn_num':nRow.cells[7].firstChild.value,
		'cost':nRow.cells[8].firstChild.value,
		'std_sale_price':nRow.cells[9].firstChild.value,
		'agent_price':nRow.cells[10].firstChild.value,
		'staff_price':nRow.cells[11].firstChild.value,
	};
	var callback = function(res){
        try {
        	if (res.code==0){
        		var sku  = res.response_content;
        		dtable.fnUpdate( sku.outer_id, nRow, 1, false );
				dtable.fnUpdate( sku.properties_alias, nRow, 3, false );
				dtable.fnUpdate( sku.wait_post_num, nRow, 5, false );
				dtable.fnUpdate( sku.remain_num, nRow, 6, false );
				dtable.fnUpdate( sku.warn_num, nRow, 7, false );
				dtable.fnUpdate( sku.cost, nRow, 8, false );
				dtable.fnUpdate( sku.std_sale_price, nRow, 9, false );
				dtable.fnUpdate( sku.agent_price, nRow, 10, false );
				dtable.fnUpdate( sku.staff_price, nRow, 11, false );
				dtable.fnUpdate( '<a class="edit"   href="#" title="修改"><icon class="icon-edit"></icon></a>'+
						'<a class="setup" href="#" title="设置"><icon class="icon-asterisk"></icon></icon></a>'+
						'<a class="remain" href="#" title="待用"><icon class="icon-pause"></icon></icon></a>'+
						'<a class="delete" href="#" title="作废"><icon class="icon-remove"></icon></icon></a>', nRow, 12, false );
				dtable.fnDraw();
				
				calProductNumAndCost();
        	}else{
        		alert("错误:"+res.response_error);
        	}
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	$.post("/items/product/"+product_id+"/"+sku_id+"/",params,callback);
}

/**将商品或规格改为待用或者作废状态*/
function delOrRemProductOrSku(nRow,status)
{
	var params = {
		'product_id':product_id,
		'sku_id':$(nRow.cells[0]).contents().get(0).nodeValue,
		'is_delete':status=='delete',
		'is_remain':status=='remain'
	};
	var callback = function(res){
        try {
        	if (res.code==0){
        		if (status=='delete'){
        			dtable.fnDeleteRow( nRow );
        		}
        		calProductNumAndCost();
        	}else{
        		alert("错误:"+res.response_error);
        	}
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	$.post("/items/podorsku/status/",params,callback);
}

function makeProductInfo(product)
{	
	$('#outer_id').val(product.outer_id);
	$('#barcode').val(product.barcode);
	$('#name').val(product.name);
	$('#remain_num').val(product.remain_num);
	$('#warn_num').val(product.warn_num);
	$('#wait_post_num').val(product.wait_post_num);
	$('#weight').val(product.weight);
	$('#cost').val(product.cost);
	$('#std_purchase_price').val(product.std_purchase_price);
	$('#std_sale_price').val(product.std_sale_price);
	$('#agent_price').val(product.agent_price);
	$('#staff_price').val(product.staff_price);
	
	$('#is_split').prop('checked',product.is_split);
	$('#sync_stock').prop('checked',product.sync_stock);
	$('#post_check').prop('checked',product.post_check);
	$('#is_match').prop('checked',product.is_match);
	$('#match_reason').val(product.match_reason);
	
	$('#buyer_prompt').val(product.buyer_prompt);
	$('#memo').val(product.memo);
}

function makeSkuBaseInfo(product)
{	
	$('#main-form').prop('action','/items/product/'+product.id+'/'+product.sku.id+'/');
	$('#sku_sync_stock').prop('checked',product.sku.sync_stock);
	$('#sku_is_match').prop('checked',product.sku.is_match);
	$('#sku_match_reason').val(product.sku.match_reason);
	$('#sku_post_check').prop('checked',product.sku.post_check);
	$('#sku_barcode').val(product.sku.barcode);
	$('#sku_buyer_prompt').val(product.sku.buyer_prompt);
	$('#sku_memo').val(product.sku.memo);
}

/**分配商品或规格线上库存（含多店铺）*/
function setupProductInfo(nRow)
{
	var outer_id  = nRow.cells[1];
	var params    = {
		"outer_id":$('#outer_id').val(),
		"outer_sku_id":$('input',outer_id).length>0?$('input',outer_id).val():outer_id.innerHTML,
	};
	var callback = function(res){
		try{
			if (res.code == 0){
				var product = res.response_content;
				$('#assign').html(product.assign_template);
				//设置规格基本信息
				makeSkuBaseInfo(product);
				var dlg = $('#product-setup-dialog').dialog({title: "规格管理对话框 <label class='label label-info'>(当前编辑："+
						product.name+"--"+product.sku.name+")</label>",width:'900'});
				
				$('#main-form').ajaxForm(function(result) { 
					if(result.code==1){
						alert('错误:'+result.response_error);
					}else{
						$('#main-form input[type="submit"]').attr('disabled',true); 
						$('#main-form .label-toast').css('display', 'inline-block');
						$('#main-form .label-toast').fadeOut( 2000 ,function(){
							$('#main-form input[type="submit"]').removeAttr("disabled"); 
						});
					} 
				})
				$('#assign-form').ajaxForm(function(result) { 
					if(result.code==1){
						alert('错误:'+result.response_error);
					}else{
						$('#assign-form input[type="submit"]').attr('disabled',true); 
						$('#assign-form .label-toast').css('display', 'inline-block');
						$('#assign-form .label-toast').fadeOut( 2000 ,function(){
							$('#assign-form input[type="submit"]').removeAttr("disabled"); 
						});
					} 
				})
			}else{
				alert('错误：'+res.response_error);
			}
		}catch(err){
			console.log('Error: (ajax callback) - ', err);
		}
	};
	$.getJSON("/items/product/assign/",params,callback);
}

$(document).ready(function(){
	
	product_id = $('#id').val();
	
	
	$.fn.dataTableExt.afnSortData['dom-input'] = function  ( oSettings, iColumn )
	{
		return $.map( oSettings.oApi._fnGetTrNodes(oSettings), function (tr, i) {
			return $('td:eq('+iColumn+') input', tr).val();
		} );
	};
	//对jquery的datatable表格进行初始化
	dtable = $('#productsku-table').dataTable({
   		//"bJQueryUI": true,
		"bAutoWidth": false, //自适应宽度
		"aaSorting": [[4, "desc"]],
		"iDisplayLength": 30,
		"aLengthMenu": [[30,60,100,-1], [30,60,100,"All"]],
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
		},
		"aoColumns": [
			null,
			null,
			null,
			null,
			{ "sSortDataType": "dom-input","sType": 'numeric' },
			null,
			null,
			null,
			null,
			null,
			null,
			null,
			null,
		],		
	});
	
	
	
	
	//初始化总库存数及总成本
	calProductNumAndCost();
	/**修改事件*/
	$('#productsku-table a.edit').live('click',function(e){
		e.preventDefault();
		var nRow = $(this).parents('tr')[0];
		if ( nEditing !== null && nEditing != nRow ) {
			restoreRow( dtable, nEditing );
			editRow( dtable, nRow );
			nEditing = nRow;
		}else {
			editRow( dtable, nRow );
			nEditing = nRow;
		}
	});
	
	/**绑定保存事件*/
	$('#productsku-table a.save').live('click', function (e) {
		e.preventDefault();
		var nRow = $(this).parents('tr')[0];
		saveProductAction(nRow);
		nEditing = null;
	});
	
	/**分配事件*/
	$('#productsku-table a.setup').live('click',function(e){
		e.preventDefault();
		var nRow = $(this).parents('tr')[0];
		setupProductInfo(nRow);
	});
	
	/**修改待用事件*/
	$('#productsku-table a.remain').live('click',function(e){
		e.preventDefault();
		if(confirm("确认将该商品状态改为待用吗？"))
		{
			var nRow = $(this).parents('tr')[0];
			delOrRemProductOrSku(nRow,'remain');
		}
	});
	
	/**作废事件*/
	$('#productsku-table a.delete').live('click',function(e){
		e.preventDefault();
		if(confirm("确认作废该商品吗？"))
		{
			var nRow = $(this).parents('tr')[0];
			delOrRemProductOrSku(nRow,'delete');
		}
	});
	
	//设置每页显示数量时，重新计算
	$("select[name='productsku-table_length']").change(function(e){
		e.preventDefault();
		calProductNumAndCost();
	});
	
	//搜索时，重新计算
	$("#productsku-table_filter input").keyup(function(e){
		e.preventDefault();
		calProductNumAndCost();
	});
	
	//分页时，重新计算
	$("#productsku-table_paginate a").click(function(e){
		e.preventDefault();
		calProductNumAndCost();
	});
	
	/**商品及规格库存修改获取*/
	$('.quantity').live('focus',function(e){
		var offset = $(this).offset();
		var is_sku = $(this).attr('sp')=='s'?true:false;
		var quantityDialog = $('#product-quantity-dialog');
		
		if (is_sku){
			$('#product-quantity-dialog input[name="num"]').val('');
			$('#product-quantity-dialog input[name="sku_id"]')
				.val($($(this).parents('tr')[0].cells[0]).contents().get(0).nodeValue);
		}

		quantityDialog.offset({top:0,left:0}).css('display','block').offset(offset).css('display','block');
		$('#product-quantity-dialog input[name="num"]').focus();
	});
	
	/**商品及规格库存修改*/
	$('.container').live('click',function(e){
		//如果点击库存修改对话框，则不需要关闭
		var target = $(e.target);
		if (target.hasClass('quantity')){
			return;
		}
		var quantityDialog = $('#product-quantity-dialog');
		if (quantityDialog.css('display') != 'none'){
			quantityDialog.hide();
		}
	});
	
	//设置编辑商品编码
	$("#product-form .code-edit").click(function(e){
		e.preventDefault();
		$('#product-form #outer_id').removeAttr('readonly');
	});
	
	$('#product-form').ajaxForm({'dataType':'json',
		'success':function(result) {
			console.log(result);
			if(result.code == 1){
				alert('错误:'+result.response_error);
			}else{
				makeProductInfo(result.response_content);
				alert('保存成功！');
			}
	}}).submit(function(){return false;});
	
	$('#quantity-form').ajaxForm(function(result) { 
		if(result.code==1){
			alert('错误:'+result.response_error);
		}else{
			var product = result.response_content;
			if (product.sku){
				$('#quantity-'+product.id+'-'+product.sku.id).val(product.sku.quantity);
			}else{
				$('#quantity-'+product.id).val(product.collect_num);
			}
			$('#product-quantity-dialog').hide();
			calProductNumAndCost();
		}
	});
	$('#reduce-num').click(function(){
		var reduce_input = $('#product-quantity-dialog input[name="reduce_num"]');
		if (this.checked){
			reduce_input.show();
			reduce_input.val($('#product-quantity-dialog input[name="num"]').val());
		}else{
			reduce_input.val(0);
			$('#product-quantity-dialog input[name="reduce_num"]').hide();
		}
	});
	/**商品规格设置事件初始化*/
	$("#tabs").tab();
})