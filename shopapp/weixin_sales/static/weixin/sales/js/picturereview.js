
$('.btn-success').live('click',function(e){
	e.preventDefault();
	var target = e.target;
	var pid = target.getAttribute('pid');
	
	var callback = function(result){
		if(result.code==1){
			alert('错误:没有记录更新！');
			return
		}
		$(target).removeClass('btn-success').html('已处理');
	};
	
	$.post("/weixin/sales/review/",{'pid':pid},callback,'json');
	
});

