$(".category_select").live("change",function(e){
	e.preventDefault();

	var target = e.target;
	var pid = target.getAttribute('pid');
	var cat_id = $(target).val();

	var url = "/items/product/"+pid+"/?format=json";
    var callback = function (res) {
     if (res.code == 0 && res.response_content.category.cid.toString() == cat_id) {
          $(target).after("<img src='/static/admin/img/icon-yes.gif '>");
      }
    };
	
	var csrf_token = document.getElementsByName("csrfmiddlewaretoken")[0].value;
    var data = {"csrfmiddlewaretoken":csrf_token,
    					"format":"json",
    					"category_id":cat_id};

    $.ajax({"url":url,"data":data,"success":callback,"type":"POST"});
});
