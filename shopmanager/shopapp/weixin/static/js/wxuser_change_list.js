
$('.btn-charge').live('click',function(e){
	e.preventDefault();
	var target = e.target;
	var sid = target.getAttribute('sid');
	
	var url = "/weixin/charge/"+sid+"/";
        var callback = function (res) {
          if (res["success"] == true) {
              $(target).attr("href",res["brand_links"]).attr("target","_blank").text('接管成功').removeClass(' btn-charge btn-primary').addClass('btn-success');
          }else{
          	$(target).removeClass().addClass("btn btn-warning").text('接管失败');
          	$(target.parentElement.parentElement).slideUp(2000);
          }
        };
	
	var csrf_token = document.getElementsByName("csrfmiddlewaretoken")[0].value;
    var data = {"csrfmiddlewaretoken":csrf_token,
    					"format":"json"};

    $.ajax({"url":url,"data":data,"success":callback,"type":"POST" });
});

