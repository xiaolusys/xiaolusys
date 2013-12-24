/**全局变量*/
var dtable = null; //datatable对象
var nEditing  = null;


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

/**修改一条datatable记录*/
function editRow ( oTable, nRow )
{
	var aData = oTable.fnGetData(nRow);
	var jqTds = $('>td', nRow);
	jqTds[6].innerHTML = '<input type="text" value="'+aData[6]+'">';
	jqTds[8].innerHTML = '<input type="text" value="'+aData[8]+'" >';
	jqTds[9].innerHTML = '<a class="save"  href="#" title="保存"><icon class="icon-ok"></icon></a>'+
						'<a class="assign" href="#" title="分配"><icon class="icon-asterisk"></icon></icon></a>'+
						'<a class="remain" href="#" title="待用"><icon class="icon-pause"></icon></icon></a>'+
						'<a class="delete" href="#" title="作废"><icon class="icon-remove"></icon></icon></a>';
}


/**保存一条datatable记录*/
function saveRow ( oTable, nRow )
{
	var jqInputs = $('input', nRow);
	oTable.fnUpdate( jqInputs[0].value, nRow, 6, false );
	oTable.fnUpdate( jqInputs[1].value, nRow, 8, false );
	oTable.fnUpdate( '<a class="edit"   href="#" title="修改"><icon class="icon-edit"></icon></a>'+
					'<a class="assign" href="#" title="分配"><icon class="icon-asterisk"></icon></icon></a>'+
					'<a class="remain" href="#" title="待用"><icon class="icon-pause"></icon></icon></a>'+
					'<a class="delete" href="#" title="作废"><icon class="icon-remove"></icon></icon></a>', nRow, 9, false );
	oTable.fnDraw();
}

/** 保存修改库存值及预留库存 */
function saveProductAction(nRow)
{
	var params = {
		'outer_id':nRow.cells[1].innerHTML,
		'outer_sku_id':nRow.cells[3].innerHTML,
		'num':nRow.cells[6].firstChild.value,
		'remain_num':nRow.cells[8].firstChild.value,
		'mode':1
	};
	var callback = function(res){
        try {
        	if (res.code==0){
        		var product  = res.response_content;
        		var quantity = remain_num = 0;
        		
        		if(!product.sku){
        			quantity    = product.collect_num;
        			remain_num  = product.remain_num;
        		}else{
        			quantity    = product.sku.quantity;
        			remain_num  = product.sku.remain_num;
        		}
				dtable.fnUpdate( quantity, nRow, 6, false );
				dtable.fnUpdate( remain_num, nRow, 8, false );
				dtable.fnUpdate( '<a class="edit"   href="#" title="修改"><icon class="icon-edit"></icon></a>'+
						'<a class="assign" href="#" title="分配"><icon class="icon-asterisk"></icon></icon></a>'+
						'<a class="remain" href="#" title="待用"><icon class="icon-pause"></icon></icon></a>'+
						'<a class="delete" href="#" title="作废"><icon class="icon-remove"></icon></icon></a>', nRow, 9, false );
				dtable.fnDraw();
        	}else{
        		alert("错误:"+res.response_error);
        	}
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
 	$.post("/items/update/stock/",params,callback);
}

/**将商品或规格改为待用或者作废状态*/
function delOrRemProductOrSku(nRow,status)
{
	var params = {
		'outer_id':nRow.cells[1].innerHTML,
		'sku_id':nRow.cells[3].innerHTML,
		'is_delete':status=='delete',
		'is_remain':status=='remain'
	};
	var that = this;
	var callback = function(res){
        try {
        	if (res.code==0){
        		dtable.fnDeleteRow( nRow );
        	}else{
        		alert("错误:"+res.response_error);
        	}
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        } 
	};
	$.post("/items/podorsku/status/",params,callback);
}


/**分配商品或规格线上库存（含多店铺）*/
function assignProductNum(nRow)
{
	var params = {
		"outer_id":nRow.cells[1].innerHTML,
		"outer_sku_id":nRow.cells[3].innerHTML,
		"format":"html"
	};
	var that = this;
	var callback = function(result){
    		$('#assgin-dialog').html(result);
    		var dlg = $('#assgin-dialog').dialog({title: "库存警告分配对话框",width:'900'});
			$('#assign-form').ajaxForm(function(result) { 
				if(result.code==1){
					alert('错误:'+result.response_error);
				}else{
					dlg.dialog('destroy');
				} 
			})
	};
	console.log('params',params);
	$.get("/items/product/assign/",params,callback);
}

$(document).ready(function(){
	
	//对jquery的datatable表格进行初始化
	dtable = $('#warn-items-table').dataTable({
   		//"bJQueryUI": true,
		"bAutoWidth": false, //自适应宽度
		"aaSorting": [[1, "asc"]],
		"iDisplayLength": 100,
		"aLengthMenu": [[100, 200, 500,-1], [100, 200, 500,"All"]],
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
	
	/**修改事件*/
	$('#warn-items-table a.edit').live('click',function(e){
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
	$('#warn-items-table a.save').live('click', function (e) {
		e.preventDefault();
		var nRow = $(this).parents('tr')[0];
		saveProductAction(nRow);
		nEditing = null;
	});
	
	/**分配事件*/
	$('#warn-items-table a.assign').live('click',function(e){
		e.preventDefault();
		var nRow = $(this).parents('tr')[0];
		assignProductNum(nRow);
	});
	
	/**待用事件*/
	$('#warn-items-table a.remain').live('click',function(e){
		e.preventDefault();
		if(confirm("确认将该商品状态改为待用吗？"))
		{
			var nRow = $(this).parents('tr')[0];
			delOrRemProductOrSku(nRow,'remain');
		}
	});
	
	/**作废事件*/
	$('#warn-items-table a.delete').live('click',function(e){
		e.preventDefault();
		if(confirm("确认作废该商品吗？"))
		{
			var nRow = $(this).parents('tr')[0];
			delOrRemProductOrSku(nRow,'delete');
		}
	});
	
})