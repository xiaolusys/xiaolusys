
//员工事件添加对话框

var initStaffEventAddDialog = function(){
	
};

var showStaffEventAddDialog = function(pos){
	var staffEventDialogDiv     = $('#add_staff_event');
	console.log('abc',staffEventDialogDiv,pos);
	staffEventDialogDiv.offset({top: pos.y,left:pos.x}); 
	staffEventDialogDiv.show();
};

var hideStaffEventAddDialog = function(){
	
};

window.onload = initStaffEventAddDialog;