var dialog = null;

$('.btn-info').live('click',function(e){
	e.preventDefault();
	var target = e.target;
	var cid = target.getAttribute('cid');
	
	$.getJSON("/app/comment/ignore/"+cid+"/",function(result){
	    if(result.code == 0){
	    	target.parentElement.parentElement.parentElement.style.display = 'none';
	    }else{
		    alert('请求错误！');	
	    }
    });
});

$('.btn-success').live('click',function(e){
	e.preventDefault();
	var target = e.target;
	var cid = target.getAttribute('cid');
	var nick = target.getAttribute('nick');
	
	$( "#explain_dialog input[name='cid']" ).val(cid);
	dialog.dialog("option", { title: '解释 [  '+nick+'  ] 的评价' });
	dialog.srcEvent = target;
	dialog.dialog("open");
	
});

$(document).ready(function(){
	$( "body" ).append('<div id="explain_dialog" style="text-align:center;display:none;">'+
					   '<form id="explain_form" method="post" action="/app/comment/explain/" >'+
					   '<input name="cid" type="hidden" value=""/>'+
					   '<textarea  name="reply" rows="5" cols="60"></textarea>'+
					   '<button id="submit" class="btn btn-large btn-primary">回复</button>'+
					   '</form></div>');
					   
	dialog = $( "#explain_dialog" ).dialog({ 
		autoOpen:false,
		title: "",
		width:600,
		close:function(e){
			$( "#explain_dialog textarea[name='reply']" ).val('');
		} 
	})
	
    $('#explain_form').ajaxForm(function(result) { 
		if(result.code==1){
			alert('错误:'+result.error_response);
			return
		}
		$(dialog.srcEvent).removeClass('btn-success').html('已回复');
		dialog.dialog("close");
	})
});