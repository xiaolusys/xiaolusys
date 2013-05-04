
//添加员工事件
var addStaffEvent = function(e){
	var url    = '/app/calendar/events/';
	var executors  = $('#executors').val();
	var start      = $('#start-datetime').val()
	var end        = $('#end-datetime').val()
	var title      = $('#event-content').val()
	
	if (start==null||start==''){
		alert('起始日期不能为空');
		return;
	};
	if (title==null||title==''){
		alert('事件内容不能为空');
		return;
	};
	
	var params = {'executor':executors,'start':start,'end':end,'title':title};
	var callback = function(data){
		if (data.code==1){
			alert('事件添加失败');
			return;
		}
		var calendar = $('#calendar');
		$.each(data.response_content, function(index, e) {
	         var event = {
	         	'id':e.id,
	         	'title':e.executor.username+':'+e.title,
	         	'start':e.start,
	         	'end':e.end,
	         	'allDay':true,
	         };
	         calendar.fullCalendar( 'renderEvent', event , true);
	    });
	    $('#add_staff_event').hide();
	    
	};
	
	$.ajax({ 
	    type: 'POST', 
	    url: url, 
	    data: params , 
	    dataType: 'json',
	    success: callback,
	});
}

//员工事件添加对话框
var initStaffEventAddDialog = function(){
	$('#btn-submit').click(addStaffEvent);
	$('#btn-cancle').click(function(e){
		$('#add_staff_event').hide();
	});
};

var showStaffEventAddDialog = function(pos){
	var staffEventDialogDiv     = $('#add_staff_event');
	console.log('abc',staffEventDialogDiv,pos);
	staffEventDialogDiv.show();
	staffEventDialogDiv.offset({'top': pos.y,'left':pos.x}); 
	
};

