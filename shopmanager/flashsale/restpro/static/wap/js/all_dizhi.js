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


function delete(){
	alert("confirm?");	
}
function init(){
	//var requestUrl = GLConfig.baseApiUrl + suffix;
	var requestUrl = "http://127.0.0.1:8000/rest/v1/address/29";
	//请求成功回调函数
	var requestCallBack = function(data){
		alert(data);
		var  address="<li   id=9> <p class='p1'>"+data.receiver_name+data.receiver_mobile+
		"</p><p class='p2'>"+data.receiver_state +"-"+ data.receiver_city+"-"+ data.receiver_district +"</p><a class='close'   onclilck='delete()'></a><i class='radio'  ></i></li>"
		
		$("ul").append(address)
		$("ul li  a").each(function () {  
            $(this).click(function(){  
                //alert($(this).text());  
                //alert(this);
                //alert($(this).parent())
                console.info($(this).parent().attr('id'));
                
                $(this).parent().remove()
                //$(this).parent().css({"color":"red","border":"2px solid red"});  //增加颜色
                
            });  
        });
		
		
	};
	// 发送请求
	$.ajax({ 
		type:'post', 
		url:requestUrl, 
		data:{}, 
		dataType:'json', 
		success:requestCallBack 
	}); 
	
	
}
