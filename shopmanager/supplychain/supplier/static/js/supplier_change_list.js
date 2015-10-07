$(".category_select").live("change",function(e){
	e.preventDefault();
	console.log('abc');
	var target = e.target;
	var sid = target.getAttribute('sid');
	var cat_id = $(target).val();
	
	var url = "/supplychain/supplier/brand/"+sid+"/";
    var callback = function (res) {
      if (res.category.toString() == cat_id) {
          $(target).after("<img src='/static/admin/img/icon-yes.gif '>");
      }
    };
	
	var csrf_token = document.getElementsByName("csrfmiddlewaretoken")[0].value;
    var data = {"csrfmiddlewaretoken":csrf_token,
    					"format":"json",
    					"category":cat_id};
    					
    var headers = {
	    'X-HTTP-Method-Override': 'PATCH'
	   };

    $.ajax({"url":url,"data":data,"success":callback,"type":"POST","headers":headers });
});

$('.btn-charge').live('click',function(e){
	e.preventDefault();
	var target = e.target;
	var sid = target.getAttribute('sid');
	
	var url = "/supplychain/supplier/brand/charge/"+sid+"/";
        var callback = function (res) {
          if (res["success"] == true) {
              $(target).attr("href",res["brand_links"]).attr("target","_blank").text('查看商品').removeClass(' btn-charge btn-primary').addClass('btn-success');
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

$('.btn-ignore').live('click',function(e){
	e.preventDefault();
	var target = e.target;
	var pid = target.getAttribute('pid');
	var status = target.getAttribute('status');
	
	var url = "/supplychain/supplier/product/"+pid+"/";
        var callback = function (res) {
          if (res["status"] != "ignored") {
            $(target.parentElement.parentElement.parentElement).slideUp();
          }
        };
	
	var csrf_token = document.getElementsByName("csrfmiddlewaretoken")[0].value;
    var data = {"status": status, 
				"csrfmiddlewaretoken":csrf_token,
				"format":"json"};
    
    var headers = {
	    'X-HTTP-Method-Override': 'PATCH'
	   };

    $.ajax({"url":url,"data":data,"success":callback,"type":"POST","headers":headers });
});

$('.btn-selected').live('click',function(e){
	e.preventDefault();
	var target = e.target;
	var pid = target.getAttribute('pid');
	
	var url = "/supplychain/supplier/product/"+pid+"/";
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

    $.ajax({"url":url,"data":data,"success":callback, "type":"POST","headers":headers });
});

$(".sale_category_select").live("change",function(e){
    e.preventDefault();

    var target = e.target;
    var spid = target.getAttribute('spid');
    var cat_id = $(target).val();

    var url = "/supplychain/supplier/product/"+ spid +"/?format=json";
    var callback = function (res) {

     if (res.sale_category.toString() == cat_id) {
          $(target).after("<img src='/static/admin/img/icon-yes.gif '>");
        }
    };
    
    var csrf_token = document.getElementsByName("csrfmiddlewaretoken")[0].value;
    var data = {"csrfmiddlewaretoken":csrf_token,
                        "format":"json",
                        "sale_category":cat_id};
	
	var headers = {
	    'X-HTTP-Method-Override': 'PATCH'
	   };
	
    $.ajax({"url":url,"data":data,"success":callback,"type":"POST", "headers":headers});
});

$(function () {

    $(".select_saletime").datepicker({
        dateFormat: "yy-mm-dd"
    }).change(function (e) {
        var slae_product = this.id;
        var sale_time = this.value;
        var sale_time_old = this.name;
        var target = e.target;
        var url = "/supplychain/supplier/select_sale_time/";
        var callback = function (res) {
            if (res == "OK") {
                $(target).after("<img src='/static/admin/img/icon-yes.gif '>");
            }
        };
        var data = {"slae_product": slae_product, "sale_time": sale_time};
        console.log("deebug data:",data);
        $.ajax({"url": url, 
        		"data": data, 
        		"success": callback, 
        		"type": "POST",
        		"error":function(){
        			alert('上架日期修改失败');
        		}});
    });
});