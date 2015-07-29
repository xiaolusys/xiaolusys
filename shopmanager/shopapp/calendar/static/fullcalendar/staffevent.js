//自定义render事件展现
var customRenderEvent = function(calendar,e){
	 var color = e.is_finished?'#5BB75B':'#3a87ad';
	 var event = {
	 	'id':e.id,
	 	'title':e.title,
	 	'start':e.start,
	 	'end':e.end,
	 	'allDay':false,
	 	'creator':e.creator,
	    'executor':e.executor,
	    'color':color
	 };
	 calendar.fullCalendar( 'renderEvent', event , true);
}

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
	$('#btn-submit').attr('disabled',false); 
	var params = {'executor':executors,'start':start,'end':end,'title':title};
	var callback = function(data){
		alert(data);
		$('#btn-submit').removeAttr('disabled');
		if (data.code==1){
			alert('事件添加失败');
			return;
		}
		var calendar = $('#calendar');
		$.each(data.response_content, function(index, e) {
			 customRenderEvent(calendar,e);
	    });
	    $('#executors').val('');
	    $('#event-content').val('');
	    $('#end-datetime').val('');
	    $('#add_staff_event').hide();
	};
	
	$.ajax({ 
	    type: 'POST', 
	    url: url, 
	    data: params , 
	    dataType: 'json',
	    success: callback
	});
}

//删除员工事件
var deleteStaffEvent = function(eventid){
	var url = "/app/calendar/delete/"+eventid+"/";
	
	var callback = function(data){
		if (data.code==1){
			alert('删除失败！');
			return;
		}
		//在日历上取消该事件
	    $('#calendar').fullCalendar('removeEvents',eventid);
	    $('#prompt-tip').hide();
	};
	
	$.ajax({ 
	    type: 'POST', 
	    url: url, 
	    data: {} , 
	    dataType: 'json',
	    success: callback,
	});
}

//完成员工事件
var completeStaffEvent = function(eventid){
	var url = "/app/calendar/complete/"+eventid+"/";
	
	var callback = function(data){
		if (data.code==1){
			alert('删除失败！');
			return;
		}
		
		var calendar = $('#calendar');
		//在日历上取消该事件
	    $('#calendar').fullCalendar('removeEvents',eventid);
		//重新render该事件
	    customRenderEvent(calendar,data.response_content);
	    
	    $('#prompt-tip').hide();
	};
	
	$.ajax({ 
	    type: 'POST', 
	    url: url, 
	    data: {} , 
	    dataType: 'json',
	    success: callback,
	});
}

//初始员工事件添加对话框
var initStaffEventAddDialog = function(){
	$('#btn-submit').click(addStaffEvent);
	$('#btn-cancle').click(function(e){
		$('#executors').val('');
		$('#end-datetime').val('');
	    $('#event-content').val('');
		$('#add_staff_event').hide();
	});
};

//显示添加事件对话框
var showStaffEventAddDialog = function(pos){
	var staffEventDialogDiv     = $('#add_staff_event');
	staffEventDialogDiv.show();
	staffEventDialogDiv.offset({'top': pos.y,'left':pos.x}); 
};

var getDurationDateString = function(df,dt){
	var weekday = ['日','一','二','三','四','五','六'];
	if (!dt){
		return (df.getMonth()+1)+'月'+df.getDate()+'日 (周'+weekday[df.getDay()]+')';
	}
	if (dt-df>24*3600*1000){
		return (df.getFullYear()%100)+'年'+(df.getMonth()+1)+'月'+df.getDate()+'日 (周'+weekday[df.getDay()]+')-'
			+(dt.getFullYear()%100)+'年'+(df.getMonth()+1)+'月'+dt.getDate()+'日 (周'+weekday[dt.getDay()]+')';
	}else{
		return (df.getMonth()+1)+'月'+df.getDate()+'日 (周'+weekday[df.getDay()]+'),'
			+(df.getHours()<12?'上午'+df.getHours()+'时':'下午'+(df.getHours()-12)+'时')+'-'
			+(dt.getHours()<12?'上午'+dt.getHours()+'时':'下午'+(dt.getHours()-12)+'时');
	}
};

//初始员工事件添加对话框
var initStaffEventTipDialog = function(){
	$('#tip-close').click(function(e){
		$('#prompt-tip').hide();
		return false;
	});
	$('#event-delete').click(function(e){
		var eventid = $(this).attr('eventid');
		deleteStaffEvent(eventid);
	});
	$('#event-complete').click(function(e){
		var eventid = $(this).attr('eventid');
		completeStaffEvent(eventid);
	});
};

//显示事件提示框
var showStaffEventTipDialog = function(event,pos){

	$('#tc-event-text').html(event.title);
	$('#event-creator').html(event.creator);
	$('#event-duration').html(getDurationDateString(event.start,event.end));
	$('#event-delete').attr('eventid',event.id.toString());
	$('#event-complete').attr('eventid',event.id.toString());
	
	var staffEventTipDiv = $('#prompt-tip');
	staffEventTipDiv.show();
	var elHeight = staffEventTipDiv.height();
	var elwidth  = staffEventTipDiv.width();
	var scrollHeight = $(document).scrollTop();
	staffEventTipDiv.offset({'top': scrollHeight+pos.y-elHeight-35,'left':pos.x-elwidth/2-10}); 
};

