/*
 * author=kaineng.fang
 * time:2015-7-30
 * 用于取到用户的所有收获地址
 * 
 * */




$(document).ready(function () {
	//alert("44");
	 //$("ul").append("<li> <p class='p1'>方 138 4956 4385</p><p class='p2'>上海市 - 杨浦区 - 国定东路200号 - 1号楼201</p><a class='close'   onclilck='delete()'></a><i class='radio'  ></i></li>")
	

  init();      


	
});




function init(){
	//var requestUrl = GLConfig.baseApiUrl + suffix;
	//var requestUrl = "http://127.0.0.1:8000/rest/v1/address/add/";
	//请求成功回调函数
	var requestUrl=GLConfig.baseApiUrl +GLConfig.get_all_address
	var requestCallBack = function(data){
	
	for(var i=0;i<data.length;i++){
		
			//alert(data.length);
			//alert(typeof(data[i].default))
			if (data[i].default==true){
		var  address="<li   id="+data[i].id+"> <p class='p1'>"+data[i].receiver_name+data[i].receiver_mobile+
		"</p><p class='p2'>"+data[i].receiver_state +"-"+ data[i].receiver_city+"-"+ data[i].receiver_district + "-"+data[i].receiver_address+"</p><a class='close'  ></a><i class='radio  radio-select'  ></i></li>"
       }
       else {
		   
		   var  address="<li   id="+data[i].id+"> <p class='p1'>"+data[i].receiver_name+data[i].receiver_mobile+
		"</p><p class='p2'>"+data[i].receiver_state +"-"+ data[i].receiver_city+"-"+ data[i].receiver_district +"-"+data[i].receiver_address+"</p><a class='close'  ></a><i class='radio '  ></i></li>"
   
	   }
		$("ul").append(address)
	}

  	$("ul li  a").each(function () {  
            $(this).click(function(){  
                //alert($(this).text());  
                //alert(this);
                //alert($(this).parent())
                console.info($(this).parent().attr('id'));
                delete_id=$(this).parent().attr('id');
                obj=$(this).parent();
                delete_address(obj,delete_id);
                //$(this).parent().remove()
                //$(this).parent().css({"color":"red","border":"2px solid red"});  //增加颜色
               
            });  
        });
        
        
  	//$("ul li  p").each(function () {  
         //   $(this).click(function(){  
         //       alert("跳转");
         //      window.location.href="shouhuodz-edit.html"
        //    });  
      //  });
        
        
        
$("ul li  i").each(function () {  
            $(this).click(function(){  
				$("ul li  i").removeClass("radio-select")//去掉之前选中的
              $(this).addClass("radio-select")//选中
                      $(this).parent().css({"color":"red","border":"2px solid red"});  //增加框
                       $(this).parent().siblings().css({"color":"","border":""});  //取消框
                       default_id=$(this).parent().attr('id');
                        obj=$(this).parent();
                       change_default(obj,default_id);
                       
                       
            });  
        });






	};
	// 发送请求
	$.ajax({ 
		type:'get', 
		url:requestUrl, 
		data:{"csrfmiddlewaretoken": csrftoken}, 
		dataType:'json', 
		success:requestCallBack 
	}); 
	
}

	
	
	function delete_address( obj,id){
	//alert(id);
	//obj.remove()     //删除地址
		//请求成功回调函数
	var requestUrl=GLConfig.baseApiUrl +GLConfig.delete_address
	var requestCallBack = function(data){
		//alert(data.ret)
		if(data.ret==true){
			obj.remove()     //删除地址
			
		}
		else{
			alert("删除失败")
			
		}
	};
	// 发送请求
	$.ajax({ 
		type:'get', 
		url:requestUrl, 
		data:{"csrfmiddlewaretoken": csrftoken,"id":id}, 
		dataType:'json', 
		success:requestCallBack 
	}); 
	
	
}
	

	function change_default( obj,id){
	//obj.remove()     //删除地址
		//请求成功回调函数
	var requestUrl=GLConfig.baseApiUrl +GLConfig.change_default
	var requestCallBack = function(data){
		if(data.ret==true){

		}
		else{
			alert("送货修改失败")
		}
	};
	// 发送请求
	$.ajax({ 
		type:'get', 
		url:requestUrl, 
		data:{"csrfmiddlewaretoken": csrftoken,"id":id}, 
		dataType:'json', 
		success:requestCallBack 
	}); 
	
	
}


