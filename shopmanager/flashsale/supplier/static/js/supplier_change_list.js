$('.btn-ignore').live('click',function(e){
	e.preventDefault();
	var target = e.target;
	var pid = target.getAttribute('pid');
	
	var url = "/flashsale/supplier/product/"+pid+"/";
        var callback = function (res) {
          if (res["status"] != "ignored") {
            $(target.parentElement.parentElement.parentElement).slideUp();
          }
        };
	
	var csrf_token = document.getElementsByName("csrfmiddlewaretoken")[0].value;
    var data = {"status": "ignored", 
    					"csrfmiddlewaretoken":csrf_token,
    					"format":"json"};
    
    var headers = {
	    'X-HTTP-Method-Override': 'PATCH'
	   };

    $.ajax({"url":url,"data":data,"success":callback,"type":"POST","headers":headers });
});

$('.btn-selecte').live('click',function(e){
	e.preventDefault();
	var target = e.target;
	var pid = target.getAttribute('pid');
	
	var url = "/flashsale/supplier/product/"+pid+"/";
    var callback = function (res) {
      if (res["status"] != "selected") {
        $(target.parentElement.parentElement.parentElement).slideUp();
      }
    };
	
	var csrf_token = document.getElementsByName("csrfmiddlewaretoken")[0].value;
    var data = {"status": "selected",
    					"csrfmiddlewaretoken":csrf_token,
    					 "format":"json"};
    					 
    var headers = {
	    'X-HTTP-Method-Override': 'PATCH'
	   };

    $.ajax({"url":url,"data":data,"success":callback, "type":"POST","headers":headers  });
});